"""
Long-term Memory (基于 PG JSONB) - Stub
"""
import structlog
from typing import Any

from app.agents.memory.base import BaseMemory

logger = structlog.get_logger(__name__)


class LongTermMemory(BaseMemory):
    async def read(self, key: str, **kwargs) -> Any:
        # TODO Step 3: select from memory_long_term
        logger.debug(f"[LongTerm] read {key} (stub)")
        return {"profile": {}, "ability_model": {}}

    async def write(self, data: dict, **kwargs) -> None:
        # TODO Step 3: MERGE INTO memory_long_term
        logger.debug(f"[LongTerm] write (stub)")

    async def search(self, query: str, top_k: int = 5, **kwargs) -> list[dict]:
        return []
