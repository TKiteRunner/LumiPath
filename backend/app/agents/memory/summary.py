"""
Summary Memory — PG + pgvector ANN 搜索。
对应表：memory_summaries（向量列 embedding 由 migration 创建）
"""
from __future__ import annotations

import json
import structlog
from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.memory.base import BaseMemory
from app.agents.llm import embed_one, vec_to_pg, DEFAULT_EMBED_MODEL
from app.db.engine import AsyncSessionLocal

logger = structlog.get_logger(__name__)


class SummaryMemory(BaseMemory):

    async def read(self, key: str, db: AsyncSession | None = None, **kwargs) -> Any:
        """按 id 或 source_id 精确读取。"""
        async with _session(db) as session:
            if key:
                row = await session.execute(
                    text("SELECT id, source_type, source_id, summary, created_at FROM memory_summaries WHERE id = :kid AND user_id = :uid"),
                    {"kid": key, "uid": self.user_id},
                )
            else:
                row = await session.execute(
                    text("SELECT id, source_type, source_id, summary, created_at FROM memory_summaries WHERE user_id = :uid ORDER BY created_at DESC LIMIT 5"),
                    {"uid": self.user_id},
                )
            return [dict(r) for r in row.mappings().all()]

    async def write(self, data: dict, db: AsyncSession | None = None, **kwargs) -> None:
        """
        写入摘要并异步生成向量。
        data 需含：summary (str), source_type (str), source_id (str|None)
        """
        summary_text: str = data.get("summary", "")
        if not summary_text:
            return

        # 向量化
        try:
            vector = await embed_one(summary_text)
            vec_str = vec_to_pg(vector)
        except Exception as exc:
            logger.warning("SummaryMemory embed failed, storing without vector", error=str(exc))
            vec_str = None

        now = datetime.now(timezone.utc)
        async with _session(db) as session:
            if vec_str:
                await session.execute(
                    text("""
                        INSERT INTO memory_summaries (id, user_id, source_type, source_id, summary, model_name, embedding, created_at, updated_at)
                        VALUES (:id, :uid, :stype, :sid, :summary, :model, :vec::vector, :now, :now)
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "uid": self.user_id,
                        "stype": data.get("source_type", "conversation"),
                        "sid": data.get("source_id"),
                        "summary": summary_text,
                        "model": DEFAULT_EMBED_MODEL,
                        "vec": vec_str,
                        "now": now,
                    },
                )
            else:
                await session.execute(
                    text("""
                        INSERT INTO memory_summaries (id, user_id, source_type, source_id, summary, created_at, updated_at)
                        VALUES (:id, :uid, :stype, :sid, :summary, :now, :now)
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "uid": self.user_id,
                        "stype": data.get("source_type", "conversation"),
                        "sid": data.get("source_id"),
                        "summary": summary_text,
                        "now": now,
                    },
                )
            await session.commit()
        logger.debug("SummaryMemory.write", user_id=self.user_id, source_type=data.get("source_type"))

    async def search(self, query: str, top_k: int = 5, db: AsyncSession | None = None, **kwargs) -> list[dict]:
        """pgvector 余弦距离 ANN 搜索。"""
        try:
            vector = await embed_one(query)
            vec_str = vec_to_pg(vector)
        except Exception as exc:
            logger.warning("SummaryMemory.search embed failed", error=str(exc))
            return []

        async with _session(db) as session:
            rows = await session.execute(
                text("""
                    SELECT id, source_type, source_id, summary,
                           1 - (embedding <-> :vec::vector) AS score
                    FROM memory_summaries
                    WHERE user_id = :uid
                      AND embedding IS NOT NULL
                    ORDER BY embedding <-> :vec::vector
                    LIMIT :k
                """),
                {"vec": vec_str, "uid": self.user_id, "k": top_k},
            )
            results = [dict(r) for r in rows.mappings().all()]
        logger.debug("SummaryMemory.search", user_id=self.user_id, query=query[:50], hits=len(results))
        return results


from contextlib import asynccontextmanager


@asynccontextmanager
async def _session(db: AsyncSession | None):
    if db is not None:
        yield db
    else:
        async with AsyncSessionLocal() as session:
            yield session
