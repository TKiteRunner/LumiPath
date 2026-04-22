"""
DailyNoteAssistantTool — 读取或创建今日 daily note，追加内容并写回 Vault。
"""
from __future__ import annotations

from datetime import date
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.tools.base import BaseTool, register_tool

logger = structlog.get_logger(__name__)


@register_tool(name="daily_note_assistant", version="1.0.0")
class DailyNoteAssistantTool(BaseTool):

    async def execute(
        self,
        user_id: str,
        content_to_append: str = "",
        note_date: str = "",
        frontmatter_patch: dict | None = None,
        db: AsyncSession | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        from app.services.notes_service import NotesService

        svc = NotesService()
        target_date = note_date or date.today().isoformat()

        # 1. 获取或创建当日笔记
        note_content, note_meta = await svc.get_or_create_daily_note(
            user_id=user_id, note_date=target_date, db=db
        )

        # 2. 追加内容
        if content_to_append:
            note_content = note_content.rstrip() + f"\n\n{content_to_append}"

        # 3. 更新 frontmatter 字段（如关联面试/OKR）
        if frontmatter_patch:
            import frontmatter as fm
            post = fm.loads(note_content)
            post.metadata.update(frontmatter_patch)
            import io
            buf = io.BytesIO()
            fm.dump(post, buf)
            note_content = buf.getvalue().decode("utf-8")

        # 4. 写回 Vault + 更新 DB
        await svc.upsert_daily_note(
            user_id=user_id, note_date=target_date, content=note_content, db=db
        )

        logger.info("DailyNoteAssistantTool", user_id=user_id, date=target_date, appended=bool(content_to_append))
        return {
            "status": "ok",
            "note_date": target_date,
            "note_id": note_meta.get("id"),
            "vault_path": note_meta.get("path"),
            "content_length": len(note_content),
        }

    @property
    def tool_schema(self) -> dict[str, Any]:
        return {
            "name": self.tool_name,
            "description": "Read or create a daily note and optionally append content or patch frontmatter fields.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content_to_append": {"type": "string", "description": "Markdown content to append"},
                    "note_date": {"type": "string", "description": "Date YYYY-MM-DD, defaults to today"},
                    "frontmatter_patch": {"type": "object", "description": "Key-value pairs to merge into frontmatter"},
                },
            },
        }
