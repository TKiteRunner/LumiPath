"""
SearchQuestionsTool — PG 全文检索 + pgvector 向量检索，RRF 融合。
"""
from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.tools.base import BaseTool, register_tool
from app.agents.llm import embed_one, vec_to_pg
from app.db.engine import AsyncSessionLocal

logger = structlog.get_logger(__name__)


@register_tool(name="search_questions", version="1.0.0")
class SearchQuestionsTool(BaseTool):

    async def execute(self, user_id: str, query: str = "", top_k: int = 10, db: AsyncSession | None = None, **kwargs) -> dict[str, Any]:
        if not query:
            return {"status": "error", "message": "query is required", "results": []}

        async with _session(db) as session:
            # ── 1. PG 全文检索（pg_trgm similarity）─────────────────────────
            ft_rows = await session.execute(
                text("""
                    SELECT iq.id, iq.question_text, iq.category, iq.difficulty, iq.tags,
                           similarity(iq.question_text, :q) AS ft_score
                    FROM interview_questions iq
                    JOIN interviews i ON i.id = iq.interview_id
                    WHERE i.user_id = :uid
                      AND similarity(iq.question_text, :q) > 0.1
                    ORDER BY ft_score DESC
                    LIMIT :k
                """),
                {"q": query, "uid": user_id, "k": top_k},
            )
            ft_results = [dict(r) for r in ft_rows.mappings().all()]

            # ── 2. pgvector 向量检索（note_embeddings 关联到题目笔记）────────
            vec_results: list[dict] = []
            try:
                vec = vec_to_pg(await embed_one(query))
                vec_rows = await session.execute(
                    text("""
                        SELECT iq.id, iq.question_text, iq.category, iq.difficulty, iq.tags,
                               1 - (ne.embedding <-> :vec::vector) AS vec_score
                        FROM interview_questions iq
                        JOIN interviews i ON i.id = iq.interview_id
                        JOIN notes n ON n.interview_id = i.id
                        JOIN note_embeddings ne ON ne.note_id = n.id
                        WHERE i.user_id = :uid
                          AND ne.embedding IS NOT NULL
                        ORDER BY ne.embedding <-> :vec::vector
                        LIMIT :k
                    """),
                    {"vec": vec, "uid": user_id, "k": top_k},
                )
                vec_results = [dict(r) for r in vec_rows.mappings().all()]
            except Exception as exc:
                logger.warning("SearchQuestions vector search failed", error=str(exc))

        # ── 3. RRF 融合 ───────────────────────────────────────────────────────
        merged = _rrf_merge(ft_results, vec_results, id_key="id", score_keys=("ft_score", "vec_score"))
        logger.info("SearchQuestionsTool", user_id=user_id, query=query[:50], hits=len(merged))
        return {"status": "ok", "query": query, "results": merged[:top_k]}

    @property
    def tool_schema(self) -> dict[str, Any]:
        return {
            "name": self.tool_name,
            "description": "Search interview questions by keyword (full-text) and semantic similarity (pgvector).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "top_k": {"type": "integer", "default": 10, "description": "Max results"},
                },
                "required": ["query"],
            },
        }


# ── helpers ───────────────────────────────────────────────────────────────────

def _rrf_merge(list_a: list[dict], list_b: list[dict], id_key: str, score_keys: tuple, k: int = 60) -> list[dict]:
    scores: dict[str, float] = {}
    items: dict[str, dict] = {}
    for ranked in [list_a, list_b]:
        for rank, item in enumerate(ranked):
            uid = str(item.get(id_key, id(item)))
            scores[uid] = scores.get(uid, 0.0) + 1.0 / (k + rank)
            items.setdefault(uid, item)
    merged = sorted(items.values(), key=lambda x: scores.get(str(x.get(id_key, id(x))), 0.0), reverse=True)
    for item in merged:
        uid = str(item.get(id_key, id(item)))
        item["rrf_score"] = round(scores.get(uid, 0.0), 6)
    return merged


from contextlib import asynccontextmanager


@asynccontextmanager
async def _session(db: AsyncSession | None):
    if db is not None:
        yield db
    else:
        async with AsyncSessionLocal() as session:
            yield session
