"""
Summary Memory (基于 PG + pgvector) - Stub
"""
import structlog
from typing import Any

from app.agents.memory.base import BaseMemory

logger = structlog.get_logger(__name__)


class SummaryMemory(BaseMemory):
    async def read(self, key: str, **kwargs) -> Any:
        return None

    async def write(self, data: dict, **kwargs) -> None:
        # TODO Step 3: insert into memory_summaries
        logger.debug(f"[Summary] write (stub)")

    async def search(self, query: str, top_k: int = 5, **kwargs) -> list[dict]:
        # TODO Step 3: embed(query) -> pgvector <-> search
        logger.debug(f"[Summary] search '{query}' (stub)")
        return []
