"""
SuggestTasksTool — 基于 OKR 上下文调用 LLM 生成每日任务建议，批量写入 daily_tasks。
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any
import uuid

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.tools.base import BaseTool, register_tool
from app.agents.llm import chat
from app.db.engine import AsyncSessionLocal

logger = structlog.get_logger(__name__)

_SUGGEST_PROMPT = """你是一位 OKR 执行教练。根据以下 OKR 信息，为用户生成今日（{date}）的任务清单。

## 当前 OKR 进度
{okr_block}

## 要求
- 输出 3~5 条具体可执行的任务
- 每条任务与某个 KR 关联
- 以 JSON 数组输出，每条结构：{{"title": "...", "description": "...", "kr_id": "...", "duration_min": 60}}
- 只输出 JSON 数组，不要有多余文字"""


@register_tool(name="suggest_tasks", version="1.0.0")
class SuggestTasksTool(BaseTool):

    async def execute(self, user_id: str, task_date: str = "", max_tasks: int = 5,
                      model: str = "gpt-4o-mini", db: AsyncSession | None = None, **kwargs) -> dict[str, Any]:
        target_date = task_date or date.today().isoformat()

        async with _session(db) as session:
            # 查最近活跃的 OKR + KR
            okr_rows = await session.execute(
                text("""
                    SELECT o.title AS obj_title, o.quarter,
                           kr.id AS kr_id, kr.title AS kr_title, kr.progress::float, kr.target::float, kr.current::float, kr.unit
                    FROM okr_objectives o
                    JOIN okr_key_results kr ON kr.objective_id = o.id
                    WHERE o.user_id = :uid AND o.status = 'active'
                      AND o.deleted_at IS NULL AND kr.deleted_at IS NULL
                    ORDER BY o.priority DESC, kr.progress ASC
                    LIMIT 10
                """),
                {"uid": user_id},
            )
            krs = [dict(r) for r in okr_rows.mappings().all()]

        if not krs:
            return {"status": "ok", "date": target_date, "tasks": [], "message": "No active OKR found"}

        # 构建 OKR 上下文
        okr_block = "\n".join(
            f"- [{kr['obj_title']} / {kr['quarter']}] KR: {kr['kr_title']} "
            f"(进度 {kr['progress']*100:.0f}%, 当前 {kr['current']} / 目标 {kr['target']} {kr['unit'] or ''}) [kr_id: {kr['kr_id']}]"
            for kr in krs
        )

        prompt = _SUGGEST_PROMPT.format(date=target_date, okr_block=okr_block)
        try:
            raw = await chat(messages=[{"role": "user", "content": prompt}], model=model, temperature=0.5)
            suggestions = json.loads(raw)[:max_tasks]
        except Exception as exc:
            logger.error("SuggestTasks LLM failed", error=str(exc))
            return {"status": "error", "message": str(exc)}

        # 写入 daily_tasks
        now = datetime.now(timezone.utc)
        async with _session(db) as session:
            for i, task in enumerate(suggestions):
                await session.execute(
                    text("""
                        INSERT INTO daily_tasks (id, user_id, kr_id, task_date, title, description, is_done, order_index, created_at, updated_at)
                        VALUES (:id, :uid, :krid, :tdate, :title, :desc, false, :idx, :now, :now)
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "uid": user_id,
                        "krid": task.get("kr_id"),
                        "tdate": target_date,
                        "title": task.get("title", "")[:255],
                        "desc": task.get("description", ""),
                        "idx": i,
                        "now": now,
                    },
                )
            await session.commit()

        logger.info("SuggestTasksTool", user_id=user_id, date=target_date, task_count=len(suggestions))
        return {"status": "ok", "date": target_date, "tasks": suggestions}

    @property
    def tool_schema(self) -> dict[str, Any]:
        return {
            "name": self.tool_name,
            "description": "Suggest and create daily tasks based on active OKR progress.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_date": {"type": "string", "description": "Target date YYYY-MM-DD, defaults to today"},
                    "max_tasks": {"type": "integer", "default": 5},
                    "model": {"type": "string", "default": "gpt-4o-mini"},
                },
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
