"""API v1 路由：Agent 对话 + WebSocket 任务推送。"""
import uuid

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_permission
from app.db.session import get_async_session
from app.schemas.agent import ChatRequest, ChatResponse, TaskStatus

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
    # TODO:
    #   1. 获取/创建 AgentSession
    #   2. 生成 task_id
    #   3. publish to RabbitMQ agent_long 队列
    #   4. return ChatResponse(session_id=..., task_id=..., status="queued")
    raise NotImplementedError


@router.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: uuid.UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_async_session)):
    """轮询任务状态（WebSocket 不可用时的降级方案）。"""
    # TODO: query task_idempotency table
    raise NotImplementedError


# ── WebSocket：流式任务进度 ────────────────────────────────────────────────────
ws_router = APIRouter(prefix="/ws", tags=["websocket"])


@ws_router.websocket("/tasks/{task_id}")
async def task_progress_ws(task_id: uuid.UUID, websocket: WebSocket):
    """
    订阅 Redis Pub/Sub channel task:{task_id}，把消息转发给前端。
    Agent 执行过程中通过 publish 推送 {"stage": "streaming", "delta": "..."} 等事件。
    """
    await websocket.accept()
    # TODO Step 3：
    #   redis = get_redis()
    #   async with redis.pubsub() as ps:
    #       await ps.subscribe(f"task:{task_id}")
    #       async for msg in ps.listen():
    #           await websocket.send_json(msg["data"])
    try:
        await websocket.send_json({"stage": "connecting", "message": "WebSocket connected (stub)"})
        await websocket.receive_text()   # 保持连接直到客户端断开
    except WebSocketDisconnect:
        pass
