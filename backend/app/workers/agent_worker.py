"""
Celery Task: 驱动 LangGraph compiled_graph，逐节点推送进度到 Redis Pub/Sub。
"""
from __future__ import annotations

import asyncio
import json
import structlog

from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(bind=True, max_retries=1, default_retry_delay=5, queue="agent_long")
def run_agent_graph(self, user_id: str, session_id: str, task_id: str, message: str):
    """
    同步 Celery task 包装 async LangGraph 调用。
    每个 Agent 节点完成后将进度 publish 到 Redis channel task:{task_id}。
    """
    asyncio.run(_run_async(self, user_id, session_id, task_id, message))


async def _run_async(task, user_id: str, session_id: str, task_id: str, message: str):
    from app.db.redis import init_redis_pool, get_redis, close_redis_pool
    from app.agents.graph import compiled_graph
    from app.agents.state import AgentState
    from langchain_core.messages import HumanMessage

    # 在 worker 进程中初始化 Redis 连接池（worker 有独立进程上下文）
    await init_redis_pool()
    redis = get_redis()
    channel = f"task:{task_id}"

    async def _publish(stage: str, data: dict | None = None) -> None:
        payload = {"stage": stage, "task_id": task_id, **(data or {})}
        await redis.publish(channel, json.dumps(payload, ensure_ascii=False, default=str))

    try:
        await _publish("started", {"message": "Agent graph starting"})

        # 更新幂等性状态
        await _update_task_status(task_id, "running")

        state: AgentState = {
            "messages": [HumanMessage(content=message)],
            "user_id": user_id,
            "session_id": session_id,
            "scratchpad": {},
            "retrieved": {},
            "token_budget": 8000,
            "next_agent": None,
            "current_agent": None,
        }

        # 流式执行 LangGraph（逐节点回调）
        final_state = state
        async for chunk in compiled_graph.astream(state, stream_mode="updates"):
            for node_name, node_output in chunk.items():
                await _publish("progress", {
                    "node": node_name,
                    "delta": _extract_delta(node_output),
                })
            final_state = {**final_state, **chunk.get(list(chunk.keys())[-1], {})}

        # 提取最终回复
        final_messages = final_state.get("messages", [])
        reply = final_messages[-1].content if final_messages else ""

        # 保存 AgentMessage 到 DB
        await _save_messages(session_id, message, reply)
        await _update_task_status(task_id, "done", result={"reply": reply})
        await _publish("done", {"reply": reply})

    except Exception as exc:
        logger.error("Agent graph failed", task_id=task_id, error=str(exc))
        await _update_task_status(task_id, "failed", result={"error": str(exc)})
        await _publish("error", {"error": str(exc)})
    finally:
        await close_redis_pool()


def _extract_delta(node_output: dict) -> str:
    """从节点输出中提取最后一条 assistant 消息内容用于流式展示。"""
    messages = node_output.get("messages", [])
    if messages:
        last = messages[-1]
        if hasattr(last, "content"):
            return str(last.content)[:500]
    return ""


async def _update_task_status(task_id: str, status: str, result: dict | None = None) -> None:
    try:
        from sqlalchemy import text, create_engine
        from app.config import settings
        engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE task_idempotency SET status = :status, result = :result::jsonb
                    WHERE idempotency_key = :key
                """),
                {
                    "status": status,
                    "result": json.dumps(result or {}, default=str),
                    "key": task_id,
                },
            )
    except Exception as exc:
        logger.warning("_update_task_status failed", task_id=task_id, error=str(exc))


async def _save_messages(session_id: str, user_message: str, assistant_reply: str) -> None:
    try:
        from sqlalchemy import text, create_engine
        from app.config import settings
        from datetime import datetime, timezone
        import uuid
        now = datetime.now(timezone.utc)
        engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
        with engine.begin() as conn:
            for role, content in [("user", user_message), ("assistant", assistant_reply)]:
                conn.execute(
                    text("""
                        INSERT INTO agent_messages (id, session_id, role, content, tokens, created_at, updated_at)
                        VALUES (:id, :sid, :role, :content, 0, :now, :now)
                    """),
                    {"id": str(uuid.uuid4()), "sid": session_id, "role": role, "content": content, "now": now},
                )
    except Exception as exc:
        logger.warning("_save_messages failed", session_id=session_id, error=str(exc))
