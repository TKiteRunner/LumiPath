"""
Procedural Memory (Tool 执行日志) - Stub
"""
import structlog
from typing import Any

from app.agents.memory.base import BaseMemory

logger = structlog.get_logger(__name__)


class ProceduralMemory(BaseMemory):
    async def read(self, tool_name: str, **kwargs) -> list[dict]:
        # TODO Step 3: select from memory_procedures order by executed_at desc limit 5
        logger.debug(f"[Procedural] read avg for {tool_name} (stub)")
        return []

    async def write(self, data: dict, **kwargs) -> None:
        # 记录执行结果
        logger.debug(f"[Procedural] write execution (stub)")

    async def search(self, query: str, top_k: int = 5, **kwargs) -> list[dict]:
        return []
