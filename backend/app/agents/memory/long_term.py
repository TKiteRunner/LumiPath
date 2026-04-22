"""
Long-term Memory — PostgreSQL JSONB merge。
对应表：memory_long_term（user_id 为主键）
"""
from __future__ import annotations

import structlog
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.memory.base import BaseMemory
from app.db.engine import AsyncSessionLocal

logger = structlog.get_logger(__name__)


class LongTermMemory(BaseMemory):

    async def read(self, key: str, db: AsyncSession | None = None, **kwargs) -> Any:
        """
        读取用户长期画像。key 为空时返回完整行 dict；
        key 非空时返回 profile/ability_model/preferences 某个子字段。
        """
        async with _session(db) as session:
            row = await session.execute(
                text("SELECT profile, ability_model, preferences FROM memory_long_term WHERE user_id = :uid"),
                {"uid": self.user_id},
            )
            result = row.mappings().one_or_none()
            if result is None:
                return {"profile": {}, "ability_model": {}, "preferences": {}}
            data = dict(result)
            if key and key in data:
                return data[key]
            return data

    async def write(self, data: dict, reason: str | None = None, db: AsyncSession | None = None, **kwargs) -> None:
        """
        JSONB merge upsert：现有字段被 data 中的相同 key 覆盖，其他字段保留。
        分 profile / ability_model / preferences 三个顶层 JSONB 列分别合并。
        """
        if not data:
            return
        now = datetime.now(timezone.utc)
        profile_patch = data.get("profile", {})
        ability_patch = data.get("ability_model", {})
        pref_patch = data.get("preferences", {})

        async with _session(db) as session:
            await session.execute(
                text("""
                    INSERT INTO memory_long_term (user_id, profile, ability_model, preferences, updated_at, version)
                    VALUES (:uid, :profile::jsonb, :ability::jsonb, :pref::jsonb, :now, 1)
                    ON CONFLICT (user_id) DO UPDATE SET
                        profile       = memory_long_term.profile       || :profile::jsonb,
                        ability_model = memory_long_term.ability_model || :ability::jsonb,
                        preferences   = memory_long_term.preferences   || :pref::jsonb,
                        updated_at    = :now,
                        version       = memory_long_term.version + 1
                """),
                {
                    "uid": self.user_id,
                    "profile": _jsonb(profile_patch),
                    "ability": _jsonb(ability_patch),
                    "pref": _jsonb(pref_patch),
                    "now": now,
                },
            )
            # 记录变更历史
            if reason or data:
                await session.execute(
                    text("INSERT INTO memory_long_term_history (user_id, diff, reason, created_at) VALUES (:uid, :diff::jsonb, :reason, :now)"),
                    {"uid": self.user_id, "diff": _jsonb(data), "reason": reason, "now": now},
                )
            await session.commit()
        logger.debug("LongTermMemory.write", user_id=self.user_id, keys=list(data.keys()))

    async def search(self, query: str, top_k: int = 5, **kwargs) -> list[dict]:
        # 长期画像为结构化数据，不做全文检索；返回单条快照
        snap = await self.read("")
        return [snap] if snap else []


# ── helpers ───────────────────────────────────────────────────────────────────

import json
from contextlib import asynccontextmanager


def _jsonb(d: dict) -> str:
    return json.dumps(d, ensure_ascii=False, default=str)


@asynccontextmanager
async def _session(db: AsyncSession | None):
    """若调用方已传入 session 则复用，否则新建独立 session。"""
    if db is not None:
        yield db
    else:
        async with AsyncSessionLocal() as session:
            yield session
