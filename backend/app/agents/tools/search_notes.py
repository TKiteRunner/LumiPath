"""
SearchNotesTool — PG pg_trgm 全文检索 + pgvector ANN，RRF 融合。
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


@register_tool(name="search_notes", version="1.0.0")
class SearchNotesTool(BaseTool):

    async def execute(self, user_id: str, query: str = "", note_type: str = "",
                      top_k: int = 5, db: AsyncSession | None = None, **kwargs) -> dict[str, Any]:
        if not query:
            return {"status": "error", "message": "query is required", "results": []}

        type_filter = "AND n.type = :ntype" if note_type else ""

        async with _session(db) as session:
            # 1. pg_trgm 相似度全文检索
            ft_rows = await session.execute(
                text(f"""
                    SELECT n.id, n.title, n.type, n.note_date, n.content_preview, n.path,
                           similarity(COALESCE(n.title,'') || ' ' || COALESCE(n.content_preview,''), :q) AS ft_score
                    FROM notes n
                    WHERE n.user_id = :uid AND n.deleted_at IS NULL {type_filter}
                      AND similarity(COALESCE(n.title,'') || ' ' || COALESCE(n.content_preview,''), :q) > 0.05
                    ORDER BY ft_score DESC
                    LIMIT :k
                """),
                {"q": query, "uid": user_id, "k": top_k, **({"ntype": note_type} if note_type else {})},
            )
            ft_results = [dict(r) for r in ft_rows.mappings().all()]

            # 2. pgvector ANN（note_embeddings）
            vec_results: list[dict] = []
            try:
                vec = vec_to_pg(await embed_one(query))
                vec_rows = await session.execute(
                    text(f"""
                        SELECT DISTINCT ON (n.id) n.id, n.title, n.type, n.note_date, n.content_preview, n.path,
                               1 - (ne.embedding <-> :vec::vector) AS vec_score
                        FROM notes n
                        JOIN note_embeddings ne ON ne.note_id = n.id
                        WHERE n.user_id = :uid AND n.deleted_at IS NULL {type_filter}
                          AND ne.embedding IS NOT NULL
                        ORDER BY n.id, ne.embedding <-> :vec::vector
                        LIMIT :k
                    """),
                    {"vec": vec, "uid": user_id, "k": top_k, **({"ntype": note_type} if note_type else {})},
                )
                vec_results = [dict(r) for r in vec_rows.mappings().all()]
            except Exception as exc:
                logger.warning("SearchNotes vector search failed", error=str(exc))

        merged = _rrf_merge(ft_results, vec_results, id_key="id")
        logger.info("SearchNotesTool", user_id=user_id, query=query[:50], hits=len(merged))
        return {"status": "ok", "query": query, "results": merged[:top_k]}

    @property
    def tool_schema(self) -> dict[str, Any]:
        return {
            "name": self.tool_name,
            "description": "Search personal notes by keyword (full-text) and semantic similarity (pgvector).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "note_type": {"type": "string", "description": "Filter by note type: daily/weekly/interview/okr/free"},
                    "top_k": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        }


def _rrf_merge(list_a: list[dict], list_b: list[dict], id_key: str, k: int = 60) -> list[dict]:
    scores: dict[str, float] = {}
    items: dict[str, dict] = {}
    for ranked in [list_a, list_b]:
        for rank, item in enumerate(ranked):
            uid = str(item.get(id_key, id(item)))
            scores[uid] = scores.get(uid, 0.0) + 1.0 / (k + rank)
            items.setdefault(uid, item)
    merged = sorted(items.values(), key=lambda x: scores.get(str(x.get(id_key, id(x))), 0.0), reverse=True)
    for item in merged:
        item["rrf_score"] = round(scores.get(str(item.get(id_key, id(item))), 0.0), 6)
    return merged


from contextlib import asynccontextmanager


@asynccontextmanager
async def _session(db: AsyncSession | None):
    if db is not None:
        yield db
    else:
        async with AsyncSessionLocal() as session:
            yield session
