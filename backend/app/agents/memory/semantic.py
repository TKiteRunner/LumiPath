"""
Semantic Memory (基于 Neo4j 图数据库) - Stub
"""
import structlog
from typing import Any

from app.agents.memory.base import BaseMemory

logger = structlog.get_logger(__name__)


class SemanticMemory(BaseMemory):
    async def read(self, key: str, **kwargs) -> Any:
        return None

    async def write(self, data: dict, **kwargs) -> None:
        # TODO Step 3: Neo4j MERGE nodes and relationships
        logger.debug(f"[Semantic] write (stub)")

    async def search(self, query: str, top_k: int = 5, **kwargs) -> list[dict]:
        # TODO Step 3: Cypher fulltext or vector search
        logger.debug(f"[Semantic] search '{query}' (stub)")
        return []
