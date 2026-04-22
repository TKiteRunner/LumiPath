"""
WebSocket 连接管理器。
每个 task_id 对应一个 WebSocket 连接，后台协程从 Redis Pub/Sub 读取
Agent 阶段性输出并转发给前端，直到收到 stage=done/error 信号。
"""
from __future__ import annotations

import asyncio
import json
import structlog
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from app.db.redis import get_redis

logger = structlog.get_logger(__name__)

# Redis channel 前缀
_CHANNEL_PREFIX = "task:"


class WebSocketManager:

    def __init__(self) -> None:
        # task_id -> WebSocket
        self._connections: dict[str, WebSocket] = {}
        # task_id -> forward task
        self._tasks: dict[str, asyncio.Task[None]] = {}

    async def connect(self, task_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections[task_id] = ws
        fwd = asyncio.create_task(
            self._forward(task_id, ws),
            name=f"ws-forward-{task_id}",
        )
        self._tasks[task_id] = fwd
        logger.info("WebSocket connected", task_id=task_id)

    async def disconnect(self, task_id: str) -> None:
        task = self._tasks.pop(task_id, None)
        if task and not task.done():
            task.cancel()
        self._connections.pop(task_id, None)
        logger.info("WebSocket disconnected", task_id=task_id)

    async def _forward(self, task_id: str, ws: WebSocket) -> None:
        """订阅 Redis Pub/Sub，将消息实时转发给 WebSocket 客户端。"""
        channel = f"{_CHANNEL_PREFIX}{task_id}"
        redis = get_redis()
        try:
            async with redis.pubsub() as ps:
                await ps.subscribe(channel)
                async for msg in ps.listen():
                    if msg["type"] != "message":
                        continue
                    raw: str = msg["data"]
                    try:
                        await ws.send_text(raw)
                    except WebSocketDisconnect:
                        break
                    try:
                        data: dict[str, Any] = json.loads(raw)
                        if data.get("stage") in ("done", "error"):
                            break
                    except json.JSONDecodeError:
                        pass
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.error("WebSocket forward error", task_id=task_id, error=str(exc))
        finally:
            await self.disconnect(task_id)

    async def publish(self, task_id: str, payload: dict[str, Any]) -> None:
        """由 Agent Worker 调用，将进度事件推送到 Redis Pub/Sub。"""
        redis = get_redis()
        await redis.publish(
            f"{_CHANNEL_PREFIX}{task_id}",
            json.dumps(payload, ensure_ascii=False, default=str),
        )


# 全局单例
ws_manager = WebSocketManager()
