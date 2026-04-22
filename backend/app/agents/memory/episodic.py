"""
Episodic Memory — PG + pgvector ANN 搜索。
对应表：memory_episodes（向量列 embedding 由 migration 创建）
"""
from __future__ import annotations

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


class EpisodicMemory(BaseMemory):

    async def read(self, key: str, db: AsyncSession | None = None, **kwargs) -> list[dict]:
        """按 id 精确读取，或按用户拉最近 10 条。"""
        async with _session(db) as session:
            if key:
                rows = await session.execute(
                    text("SELECT id, title, occurred_at, narrative, context, importance FROM memory_episodes WHERE id = :kid AND user_id = :uid"),
                    {"kid": key, "uid": self.user_id},
                )
            else:
                rows = await session.execute(
                    text("SELECT id, title, occurred_at, narrative, context, importance FROM memory_episodes WHERE user_id = :uid ORDER BY occurred_at DESC LIMIT 10"),
                    {"uid": self.user_id},
                )
            return [dict(r) for r in rows.mappings().all()]

    async def write(self, data: dict, db: AsyncSession | None = None, **kwargs) -> None:
        """
        写入情景记忆并生成向量。
        data 需含：title (str), narrative (str), occurred_at (datetime|None)
        """
        narrative: str = data.get("narrative", "")
        title: str = data.get("title", "Untitled")
        if not narrative:
            return

        # 向量化 title + narrative
        try:
            vector = await embed_one(f"{title}\n{narrative}")
            vec_str = vec_to_pg(vector)
        except Exception as exc:
            logger.warning("EpisodicMemory embed failed", error=str(exc))
            vec_str = None

        occurred_at = data.get("occurred_at") or datetime.now(timezone.utc)
        import json as _json

        async with _session(db) as session:
            if vec_str:
                await session.execute(
                    text("""
                        INSERT INTO memory_episodes
                            (id, user_id, title, occurred_at, narrative, context, importance, model_name, embedding, created_at, updated_at)
                        VALUES
                            (:id, :uid, :title, :occ, :narrative, :ctx::jsonb, :imp, :model, :vec::vector, :now, :now)
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "uid": self.user_id,
                        "title": title,
                        "occ": occurred_at,
                        "narrative": narrative,
                        "ctx": _json.dumps(data.get("context", {}), default=str),
                        "imp": data.get("importance", 5),
                        "model": DEFAULT_EMBED_MODEL,
                        "vec": vec_str,
                        "now": datetime.now(timezone.utc),
                    },
                )
            else:
                await session.execute(
                    text("""
                        INSERT INTO memory_episodes
                            (id, user_id, title, occurred_at, narrative, context, importance, created_at, updated_at)
                        VALUES
                            (:id, :uid, :title, :occ, :narrative, :ctx::jsonb, :imp, :now, :now)
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "uid": self.user_id,
                        "title": title,
                        "occ": occurred_at,
                        "narrative": narrative,
                        "ctx": _json.dumps(data.get("context", {}), default=str),
                        "imp": data.get("importance", 5),
                        "now": datetime.now(timezone.utc),
                    },
                )
            await session.commit()
        logger.debug("EpisodicMemory.write", user_id=self.user_id, title=title)

    async def search(self, query: str, top_k: int = 5, db: AsyncSession | None = None, **kwargs) -> list[dict]:
        """pgvector 余弦距离 ANN 搜索。"""
        try:
            vector = await embed_one(query)
            vec_str = vec_to_pg(vector)
        except Exception as exc:
            logger.warning("EpisodicMemory.search embed failed", error=str(exc))
            return []

        async with _session(db) as session:
            rows = await session.execute(
                text("""
                    SELECT id, title, occurred_at, narrative, importance,
                           1 - (embedding <-> :vec::vector) AS score
                    FROM memory_episodes
                    WHERE user_id = :uid
                      AND embedding IS NOT NULL
                    ORDER BY embedding <-> :vec::vector
                    LIMIT :k
                """),
                {"vec": vec_str, "uid": self.user_id, "k": top_k},
            )
            results = [dict(r) for r in rows.mappings().all()]
        logger.debug("EpisodicMemory.search", user_id=self.user_id, query=query[:50], hits=len(results))
        return results


from contextlib import asynccontextmanager


@asynccontextmanager
async def _session(db: AsyncSession | None):
    if db is not None:
        yield db
    else:
        async with AsyncSessionLocal() as session:
            yield session
