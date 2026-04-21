"""
Episodic Memory (基于 PG + pgvector) - Stub
"""
import structlog
from typing import Any

from app.agents.memory.base import BaseMemory

logger = structlog.get_logger(__name__)


class EpisodicMemory(BaseMemory):
    async def read(self, key: str, **kwargs) -> list[dict]:
        return []

    async def write(self, data: dict, **kwargs) -> None:
        # TODO Step 3: insert into memory_episodes
        logger.debug(f"[Episodic] write (stub)")

    async def search(self, query: str, top_k: int = 5, **kwargs) -> list[dict]:
        # TODO Step 3: pgvector similarity search
        logger.debug(f"[Episodic] search '{query}' (stub)")
        return []
