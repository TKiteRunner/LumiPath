"""
ListNotesTool — 列出用户笔记，支持月份过滤和标签过滤。
主要供 MCP 客户端（Claude Desktop / Cursor / Obsidian）调用。
"""
from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.tools.base import BaseTool, register_tool
from app.db.engine import AsyncSessionLocal
from contextlib import asynccontextmanager

logger = structlog.get_logger(__name__)


@register_tool(name="list_notes", version="1.0.0")
class ListNotesTool(BaseTool):

    async def execute(
        self,
        user_id: str,
        month: str = "",
        tag: str = "",
        limit: int = 20,
        db: AsyncSession | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        async with _session(db) as session:
            conditions = ["n.user_id = :uid", "n.deleted_at IS NULL"]
            params: dict[str, Any] = {"uid": user_id, "limit": min(limit, 100)}

            if month:
                conditions.append("TO_CHAR(n.note_date, 'YYYY-MM') = :month")
                params["month"] = month

            if tag:
                conditions.append(
                    "EXISTS (SELECT 1 FROM note_tags nt WHERE nt.note_id = n.id AND nt.tag = :tag)"
                )
                params["tag"] = tag

            where = " AND ".join(conditions)
            rows = await session.execute(
                text(f"""
                    SELECT
                        n.id,
                        TO_CHAR(n.note_date, 'YYYY-MM-DD') AS date,
                        n.title,
                        n.word_count,
                        n.updated_at,
                        COALESCE(
                            (SELECT json_agg(nt.tag ORDER BY nt.tag)
                             FROM note_tags nt WHERE nt.note_id = n.id),
                            '[]'::json
                        ) AS tags
                    FROM notes n
                    WHERE {where}
                    ORDER BY n.note_date DESC
                    LIMIT :limit
                """),
                params,
            )
            notes = [dict(r) for r in rows.mappings().all()]

        logger.info("ListNotesTool", user_id=user_id, month=month, tag=tag, count=len(notes))
        return {"status": "ok", "notes": notes, "count": len(notes)}

    @property
    def tool_schema(self) -> dict[str, Any]:
        return {
            "name": self.tool_name,
            "description": (
                "List the user's daily study notes. "
                "Supports optional month filter (YYYY-MM) and tag filter. "
                "Returns date, title, word count, and tags."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID"},
                    "month": {
                        "type": "string",
                        "description": "Filter by month in YYYY-MM format. Omit for recent 20.",
                    },
                    "tag": {
                        "type": "string",
                        "description": "Filter by a specific tag.",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 20,
                        "description": "Maximum number of notes to return (max 100).",
                    },
                },
                "required": ["user_id"],
            },
        }


@asynccontextmanager
async def _session(db: AsyncSession | None):
    if db is not None:
        yield db
    else:
        async with AsyncSessionLocal() as session:
            yield session
