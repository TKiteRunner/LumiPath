"""
GetNoteByDateTool — 按日期精确获取笔记的完整 Markdown 内容及 frontmatter。
主要供 MCP 客户端调用，支持 Agent 读取特定日期笔记进行分析。
"""
from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.tools.base import BaseTool, register_tool
from app.db.engine import AsyncSessionLocal
from app.services.notes_service import NotesService
from contextlib import asynccontextmanager

logger = structlog.get_logger(__name__)


@register_tool(name="get_note_by_date", version="1.0.0")
class GetNoteByDateTool(BaseTool):

    async def execute(
        self,
        user_id: str,
        date: str,
        db: AsyncSession | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        读取指定日期的笔记。
        1. 先查 DB 获取 note 元数据（路径、frontmatter）。
        2. 再从文件系统读取完整 Markdown 内容。
        3. 同时返回反向链接列表。
        """
        async with _session(db) as session:
            # 查询 DB 元数据
            row = await session.execute(
                text("""
                    SELECT
                        n.id,
                        n.file_path,
                        n.title,
                        n.word_count,
                        n.frontmatter,
                        TO_CHAR(n.note_date, 'YYYY-MM-DD') AS date,
                        COALESCE(
                            (SELECT json_agg(nt.tag ORDER BY nt.tag)
                             FROM note_tags nt WHERE nt.note_id = n.id),
                            '[]'::json
                        ) AS tags
                    FROM notes n
                    WHERE n.user_id = :uid
                      AND TO_CHAR(n.note_date, 'YYYY-MM-DD') = :date
                      AND n.deleted_at IS NULL
                    LIMIT 1
                """),
                {"uid": user_id, "date": date},
            )
            note_row = row.mappings().first()

            if not note_row:
                return {
                    "status": "not_found",
                    "message": f"No note found for date {date}",
                    "date": date,
                }

            # 从文件系统读取完整内容
            svc = NotesService()
            try:
                content = await svc.read_note_content(note_row["file_path"])
            except Exception as e:
                logger.warning("GetNoteByDateTool: file read failed", error=str(e))
                content = ""

            # 查询反向链接
            backlinks_rows = await session.execute(
                text("""
                    SELECT
                        TO_CHAR(src.note_date, 'YYYY-MM-DD') AS source_date,
                        src.title AS source_title
                    FROM note_links nl
                    JOIN notes src ON src.id = nl.source_note_id
                    WHERE nl.target_note_id = :note_id AND src.deleted_at IS NULL
                    ORDER BY src.note_date DESC
                    LIMIT 10
                """),
                {"note_id": note_row["id"]},
            )
            backlinks = [dict(r) for r in backlinks_rows.mappings().all()]

        logger.info("GetNoteByDateTool", user_id=user_id, date=date)
        return {
            "status": "ok",
            "note": {
                "id": note_row["id"],
                "date": note_row["date"],
                "title": note_row["title"],
                "word_count": note_row["word_count"],
                "tags": note_row["tags"],
                "frontmatter": note_row["frontmatter"],
                "content": content,
            },
            "backlinks": backlinks,
        }

    @property
    def tool_schema(self) -> dict[str, Any]:
        return {
            "name": self.tool_name,
            "description": (
                "Retrieve the full Markdown content and metadata of a user's daily note "
                "by exact date. Returns content, frontmatter fields (mood, energy, tags, "
                "related_interviews, related_okr), and backlinks."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID"},
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format, e.g. 2026-04-22",
                    },
                },
                "required": ["user_id", "date"],
            },
        }


@asynccontextmanager
async def _session(db: AsyncSession | None):
    if db is not None:
        yield db
    else:
        async with AsyncSessionLocal() as session:
            yield session
