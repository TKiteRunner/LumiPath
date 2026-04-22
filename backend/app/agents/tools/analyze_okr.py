"""
AnalyzeOKRTool — 查询 OKR 进度，衍生计算加权完成率。
"""
from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.tools.base import BaseTool, register_tool
from app.db.engine import AsyncSessionLocal

logger = structlog.get_logger(__name__)


@register_tool(name="analyze_okr", version="1.0.0")
class AnalyzeOKRTool(BaseTool):

    async def execute(self, user_id: str, quarter: str = "", db: AsyncSession | None = None, **kwargs) -> dict[str, Any]:
        async with _session(db) as session:
            q_filter = "AND o.quarter = :quarter" if quarter else ""
            obj_rows = await session.execute(
                text(f"""
                    SELECT o.id, o.title, o.quarter, o.status, o.progress::float AS progress,
                           o.priority, o.motivation
                    FROM okr_objectives o
                    WHERE o.user_id = :uid AND o.deleted_at IS NULL {q_filter}
                    ORDER BY o.priority DESC, o.quarter DESC
                """),
                {"uid": user_id, "quarter": quarter} if quarter else {"uid": user_id},
            )
            objectives = []
            for obj in obj_rows.mappings().all():
                obj_dict = dict(obj)
                # 拉该 objective 下的 KR
                kr_rows = await session.execute(
                    text("""
                        SELECT id, title, metric, baseline::float, target::float,
                               current::float, unit, weight::float, progress::float, status
                        FROM okr_key_results
                        WHERE objective_id = :oid AND deleted_at IS NULL
                        ORDER BY created_at
                    """),
                    {"oid": obj_dict["id"]},
                )
                krs = [dict(r) for r in kr_rows.mappings().all()]
                # 加权进度
                if krs:
                    total_weight = sum(kr["weight"] for kr in krs) or 1.0
                    weighted_progress = sum(kr["progress"] * kr["weight"] for kr in krs) / total_weight
                else:
                    weighted_progress = obj_dict["progress"]
                obj_dict["key_results"] = krs
                obj_dict["weighted_progress"] = round(weighted_progress, 4)
                obj_dict["at_risk"] = weighted_progress < 0.3
                objectives.append(obj_dict)

        logger.info("AnalyzeOKRTool", user_id=user_id, quarter=quarter, obj_count=len(objectives))
        return {"status": "ok", "quarter": quarter, "objectives": objectives}

    @property
    def tool_schema(self) -> dict[str, Any]:
        return {
            "name": self.tool_name,
            "description": "Analyze OKR progress and compute weighted completion rate per objective.",
            "parameters": {
                "type": "object",
                "properties": {
                    "quarter": {"type": "string", "description": "Quarter identifier, e.g. '2026-Q2'. Omit for all quarters."},
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
