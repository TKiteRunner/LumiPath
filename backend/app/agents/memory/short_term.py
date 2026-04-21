"""
Short-term Memory (基于 Redis) - Stub
"""
import structlog
from typing import Any

from app.agents.memory.base import BaseMemory

logger = structlog.get_logger(__name__)


class ShortTermMemory(BaseMemory):
    async def read(self, key: str, **kwargs) -> Any:
        # TODO Step 3: Redis GET/HGET
        logger.debug(f"[ShortTerm] read {key} (stub)")
        return None

    async def write(self, data: dict, **kwargs) -> None:
        # TODO Step 3: Redis pipeline HSET / ZADD
        logger.debug(f"[ShortTerm] write {data.keys()} (stub)")

    async def search(self, query: str, top_k: int = 5, **kwargs) -> list[dict]:
        # Redis 不全文检索，只有 key 读写
        return []
