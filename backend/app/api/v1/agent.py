"""API v1 路由：Agent 对话 + WebSocket 任务推送。"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_permission
from app.db.session import get_async_session
from app.schemas.agent import ChatRequest, ChatResponse, TaskStatus
from app.websocket.manager import ws_manager

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=202,
    dependencies=[require_permission("agent:invoke")],
)
async def chat(
    body: ChatRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
):
    """
    触发 LangGraph Supervisor，返回 task_id（202 Accepted）。
    客户端随后通过 WS /ws/tasks/{task_id} 订阅实时进度。
    """
    from app.models.agent import AgentSession
    from sqlalchemy import select, insert

    # 1. 获取或创建 AgentSession
    session_id_input = body.session_id
    if session_id_input:
        agent_session = (
            await db.execute(
                select(AgentSession).where(
                    AgentSession.id == uuid.UUID(str(session_id_input)),
                    AgentSession.user_id == current_user.id,
                )
            )
        ).scalar_one_or_none()
    else:
        agent_session = None

    if not agent_session:
        agent_session = AgentSession(
            user_id=current_user.id,
            thread_id=str(uuid.uuid4()),
            status="active",
        )
        db.add(agent_session)
        await db.flush()

    # 2. 生成 task_id + 写幂等性记录
    task_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    await db.execute(
        text("""
            INSERT INTO task_idempotency (idempotency_key, task_id, status, created_at)
            VALUES (:key, :tid::uuid, 'queued', :now)
            ON CONFLICT (idempotency_key) DO NOTHING
        """),
        {"key": task_id, "tid": task_id, "now": now},
    )
    await db.commit()

    # 3. 投递 Celery agent_long 队列
    from app.workers.agent_worker import run_agent_graph
    run_agent_graph.apply_async(
        args=[str(current_user.id), str(agent_session.id), task_id, body.message],
        queue="agent_long",
        task_id=task_id,
    )

    return ChatResponse(
        session_id=str(agent_session.id),
        task_id=task_id,
        status="queued",
    )


@router.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(
    task_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
):
    """轮询任务状态（WebSocket 不可用时的降级方案）。"""
    row = (
        await db.execute(
            text("SELECT status, result FROM task_idempotency WHERE idempotency_key = :key"),
            {"key": str(task_id)},
        )
    ).mappings().one_or_none()

    if not row:
        return TaskStatus(task_id=str(task_id), status="not_found")
    return TaskStatus(
        task_id=str(task_id),
        status=row["status"] or "unknown",
        result=row["result"],
    )


# ── WebSocket：流式任务进度 ────────────────────────────────────────────────────
ws_router = APIRouter(prefix="/ws", tags=["websocket"])


@ws_router.websocket("/tasks/{task_id}")
async def task_progress_ws(task_id: uuid.UUID, websocket: WebSocket):
    """
    订阅 Redis Pub/Sub channel task:{task_id}，把消息实时转发给前端。
    Agent Worker 执行过程中 publish {"stage": "progress"|"done"|"error", ...} 事件。
    """
    await ws_manager.connect(str(task_id), websocket)
    try:
        # 保持连接：_forward 协程在 done/error 后会自动断开
        while str(task_id) in ws_manager._connections:
            await asyncio.sleep(30)  # 心跳检测间隔
    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(str(task_id))
