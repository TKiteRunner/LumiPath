"""
GenerateReportTool — OKR + 笔记上下文 → LLM → 生成季度/周报 md，写入 Vault。
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.tools.base import BaseTool, register_tool
from app.agents.llm import chat
from app.config import settings
from app.db.engine import AsyncSessionLocal

logger = structlog.get_logger(__name__)

_REPORT_PROMPT = """你是一位职业成长教练，请根据以下信息生成一份{report_type}成长报告（Markdown 格式）。

## OKR 进度
{okr_block}

## 近期笔记摘要
{notes_block}

## 报告要求
- 标题：# {title}
- 章节：## 目标完成情况、## 本期亮点、## 遇到的挑战、## 下期重点
- 语言：中文，专业且有洞察力
- 长度：500-800字"""


@register_tool(name="generate_report", version="1.0.0")
class GenerateReportTool(BaseTool):

    async def execute(self, user_id: str, report_type: str = "weekly", period_start: str = "",
                      model: str = "gpt-4o-mini", db: AsyncSession | None = None, **kwargs) -> dict[str, Any]:
        start_date = date.fromisoformat(period_start) if period_start else date.today() - timedelta(days=7)
        days = 30 if report_type == "monthly" else 7
        end_date = start_date + timedelta(days=days)

        async with _session(db) as session:
            # OKR 进度
            okr_rows = await session.execute(
                text("""
                    SELECT o.title, o.quarter, o.progress::float,
                           COUNT(kr.id) AS kr_count,
                           AVG(kr.progress::float) AS avg_kr_progress
                    FROM okr_objectives o
                    LEFT JOIN okr_key_results kr ON kr.objective_id = o.id AND kr.deleted_at IS NULL
                    WHERE o.user_id = :uid AND o.deleted_at IS NULL
                    GROUP BY o.id, o.title, o.quarter, o.progress
                    ORDER BY o.priority DESC LIMIT 5
                """),
                {"uid": user_id},
            )
            okr_list = [dict(r) for r in okr_rows.mappings().all()]

            # 近期笔记摘要
            note_rows = await session.execute(
                text("""
                    SELECT title, content_preview, note_date
                    FROM notes
                    WHERE user_id = :uid AND deleted_at IS NULL
                      AND note_date BETWEEN :start AND :end
                    ORDER BY note_date DESC LIMIT 10
                """),
                {"uid": user_id, "start": start_date, "end": end_date},
            )
            notes_list = [dict(r) for r in note_rows.mappings().all()]

        okr_block = "\n".join(
            f"- {o['title']} ({o['quarter']}) 进度 {o['avg_kr_progress']*100:.0f}%" if o['avg_kr_progress'] else f"- {o['title']} ({o['quarter']})"
            for o in okr_list
        ) or "（无 OKR 数据）"
        notes_block = "\n".join(
            f"- [{n['note_date']}] {n['title']}: {(n['content_preview'] or '')[:100]}"
            for n in notes_list
        ) or "（无笔记数据）"

        type_cn = "周报" if report_type == "weekly" else "月报"
        title = f"{start_date} {type_cn}"
        prompt = _REPORT_PROMPT.format(
            report_type=type_cn, okr_block=okr_block,
            notes_block=notes_block, title=title,
        )

        try:
            report_md = await chat(messages=[{"role": "user", "content": prompt}], model=model, max_tokens=2000)
        except Exception as exc:
            logger.error("GenerateReport LLM failed", error=str(exc))
            return {"status": "error", "message": str(exc)}

        # 写入 Vault
        vault_dir = Path(settings.vault_base_path) / user_id / report_type
        vault_dir.mkdir(parents=True, exist_ok=True)
        report_path = vault_dir / f"{start_date}.md"
        report_path.write_text(report_md, encoding="utf-8")

        logger.info("GenerateReportTool", user_id=user_id, report_type=report_type, path=str(report_path))
        return {"status": "ok", "report_type": report_type, "period_start": str(start_date), "vault_path": str(report_path), "report": report_md}

    @property
    def tool_schema(self) -> dict[str, Any]:
        return {
            "name": self.tool_name,
            "description": "Generate a weekly or monthly growth report using OKR and notes, then save to Vault.",
            "parameters": {
                "type": "object",
                "properties": {
                    "report_type": {"type": "string", "enum": ["weekly", "monthly"], "default": "weekly"},
                    "period_start": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "model": {"type": "string", "default": "gpt-4o-mini"},
                },
                "required": ["period_start"],
            },
        }


from contextlib import asynccontextmanager


@asynccontextmanager
async def _session(db: AsyncSession | None):
    if db is not None:
        yield db
    else:
        async with AsyncSessionLocal() as session:
            yield session
