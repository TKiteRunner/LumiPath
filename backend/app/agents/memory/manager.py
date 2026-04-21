"""
MemoryManager: 统一调度 7 层记忆，实现 RRF 并行召回。
"""
import asyncio
from typing import Any

from app.agents.state import AgentState
from app.agents.memory.in_context import InContextMemory
from app.agents.memory.short_term import ShortTermMemory
from app.agents.memory.long_term import LongTermMemory
from app.agents.memory.summary import SummaryMemory
from app.agents.memory.episodic import EpisodicMemory
from app.agents.memory.semantic import SemanticMemory
from app.agents.memory.procedural import ProceduralMemory


class MemoryManager:
    def __init__(self, user_id: str, state: AgentState | None = None):
        self.user_id = user_id
        self.in_context = InContextMemory(user_id, state) if state else None
        self.short_term = ShortTermMemory(user_id)
        self.long_term = LongTermMemory(user_id)
        self.summary = SummaryMemory(user_id)
        self.episodic = EpisodicMemory(user_id)
        self.semantic = SemanticMemory(user_id)
        self.procedural = ProceduralMemory(user_id)

    async def retrieve_context(self, query: str) -> dict[str, Any]:
        """
        三路并行召回并 RRF 融合。
        合并长期和短期快照为 constant context。
        """
        results: dict[str, Any] = {
            "long_term": await self.long_term.read(""),
            "short_term": await self.short_term.read(""),
        }

        # 并发检索
        tasks = [
            self.summary.search(query),
            self.episodic.search(query),
            self.semantic.search(query),
        ]
        sum_rows, epi_rows, sem_rows = await asyncio.gather(*tasks)

        # TODO: RRF (Reciprocal Rank Fusion) 融合逻辑
        # 现为 stub，直接返回
        results["fused_context"] = {
            "summaries": sum_rows,
            "episodes": epi_rows,
            "semantics": sem_rows,
        }
        return results

    async def consolidate(self) -> None:
        """记忆固化：ST -> LT, 触发归档等。通常由 celery 异步调用。"""
        pass
