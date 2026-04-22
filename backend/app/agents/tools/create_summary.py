"""
CreateSummaryTool — 对内容调用 LLM 生成压缩摘要，写入 memory_summaries（含 pgvector）。
"""
from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.tools.base import BaseTool, register_tool
from app.agents.llm import chat
from app.agents.memory.summary import SummaryMemory

logger = structlog.get_logger(__name__)

_SUMMARIZE_PROMPT = """请将以下内容压缩成一段简洁的摘要（150字以内），保留关键信息和重要细节：

{content}

只输出摘要正文，不要有任何前缀或说明。"""


@register_tool(name="create_summary", version="1.0.0")
class CreateSummaryTool(BaseTool):

    async def execute(self, user_id: str, content: str = "", source_type: str = "conversation",
                      source_id: str | None = None, model: str = "gpt-4o-mini",
                      db: AsyncSession | None = None, **kwargs) -> dict[str, Any]:
        if not content:
            return {"status": "error", "message": "content is required"}

        # LLM 生成摘要
        try:
            summary_text = await chat(
                messages=[{"role": "user", "content": _SUMMARIZE_PROMPT.format(content=content[:4000])}],
                model=model,
                temperature=0.3,
                max_tokens=300,
            )
        except Exception as exc:
            logger.error("CreateSummary LLM failed", error=str(exc))
            return {"status": "error", "message": str(exc)}

        # 写入 memory_summaries（含向量）
        mem = SummaryMemory(user_id)
        await mem.write(
            data={"summary": summary_text, "source_type": source_type, "source_id": source_id},
            db=db,
        )

        logger.info("CreateSummaryTool", user_id=user_id, source_type=source_type, summary_len=len(summary_text))
        return {"status": "ok", "summary": summary_text, "source_type": source_type}

    @property
    def tool_schema(self) -> dict[str, Any]:
        return {
            "name": self.tool_name,
            "description": "Summarize text with LLM and store the result in memory_summaries with vector embedding.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Text to summarize"},
                    "source_type": {"type": "string", "description": "conversation/interview/weekly/monthly", "default": "conversation"},
                    "source_id": {"type": "string", "description": "Optional UUID of the source record"},
                    "model": {"type": "string", "default": "gpt-4o-mini"},
                },
                "required": ["content"],
            },
        }
