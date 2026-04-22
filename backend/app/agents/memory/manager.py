"""
MemoryManager: 统一调度 7 层记忆，并行召回 + RRF 融合。
"""
from __future__ import annotations

import asyncio
from typing import Any

import structlog

from app.agents.state import AgentState
from app.agents.memory.in_context import InContextMemory
from app.agents.memory.short_term import ShortTermMemory
from app.agents.memory.long_term import LongTermMemory
from app.agents.memory.summary import SummaryMemory
from app.agents.memory.episodic import EpisodicMemory
from app.agents.memory.semantic import SemanticMemory
from app.agents.memory.procedural import ProceduralMemory

logger = structlog.get_logger(__name__)

# RRF 标准超参数
_RRF_K = 60


def _rrf_score(rank: int) -> float:
    """Reciprocal Rank Fusion 单条得分：1 / (k + rank)。"""
    return 1.0 / (_RRF_K + rank)


def _rrf_fuse(ranked_lists: list[list[dict]], id_key: str = "id") -> list[dict]:
    """
    多路检索结果 RRF 融合。
    每个 list 中的 dict 需含 id_key 字段（用于去重合并）。
    返回按 rrf_score 降序排列的融合列表。
    """
    scores: dict[str, float] = {}
    items: dict[str, dict] = {}

    for ranked in ranked_lists:
        for rank, item in enumerate(ranked):
            uid = str(item.get(id_key, id(item)))
            scores[uid] = scores.get(uid, 0.0) + _rrf_score(rank)
            items.setdefault(uid, item)

    merged = sorted(items.values(), key=lambda x: scores.get(str(x.get(id_key, id(x))), 0.0), reverse=True)
    for item in merged:
        uid = str(item.get(id_key, id(item)))
        item["_rrf_score"] = round(scores.get(uid, 0.0), 6)
    return merged


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
        并行检索 summary / episodic / semantic 三层（向量语义），
        + 串行读取 long_term / short_term（固定快照），
        最终 RRF 融合返回。
        """
        # 固定快照（非检索型，直接读取）
        long_term_snap, short_term_snap = await asyncio.gather(
            self.long_term.read(""),
            self.short_term.read(""),
        )

        # 语义检索（并行）
        try:
            sum_rows, epi_rows, sem_rows = await asyncio.gather(
                self.summary.search(query),
                self.episodic.search(query),
                self.semantic.search(query),
            )
        except Exception as exc:
            logger.warning("memory parallel search failed", error=str(exc))
            sum_rows, epi_rows, sem_rows = [], [], []

        # RRF 融合三路向量召回
        fused = _rrf_fuse([sum_rows, epi_rows, sem_rows])

        logger.debug(
            "memory retrieved",
            user_id=self.user_id,
            summary_hits=len(sum_rows),
            episodic_hits=len(epi_rows),
            semantic_hits=len(sem_rows),
            fused_total=len(fused),
        )

        return {
            "long_term": long_term_snap,
            "short_term": short_term_snap,
            "fused_context": {
                "summaries": sum_rows,
                "episodes": epi_rows,
                "semantics": sem_rows,
                "rrf_merged": fused,
            },
        }

    async def consolidate(self) -> None:
        """
        记忆固化：将短期记忆摘要写入长期；触发情景归档。
        Step 3 接入真实 IO（Redis → PG）。
        """
        short_snap = await self.short_term.read("")
        if short_snap:
            await self.long_term.write({"consolidated_from_short_term": short_snap})
        logger.info("memory consolidated (stub)", user_id=self.user_id)
