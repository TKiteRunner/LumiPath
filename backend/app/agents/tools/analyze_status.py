"""
AnalyzeStatusTool — 聚合查询用户面试状态分布与近期通过率。
"""
from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.tools.base import BaseTool, register_tool
from app.db.engine import AsyncSessionLocal

logger = structlog.get_logger(__name__)


@register_tool(name="analyze_status", version="1.0.0")
class AnalyzeStatusTool(BaseTool):

    async def execute(self, user_id: str, days: int = 30, db: AsyncSession | None = None, **kwargs) -> dict[str, Any]:
        async with _session(db) as session:
            # 各状态计数
            status_rows = await session.execute(
                text("""
                    SELECT status, COUNT(*) AS cnt
                    FROM interviews
                    WHERE user_id = :uid AND deleted_at IS NULL
                    GROUP BY status ORDER BY cnt DESC
                """),
                {"uid": user_id},
            )
            status_counts = {r["status"]: r["cnt"] for r in status_rows.mappings().all()}

            # 近 N 天通过率
            rate_row = await session.execute(
                text("""
                    SELECT
                        COUNT(*) FILTER (WHERE status IN ('passed','offer'))::float /
                        NULLIF(COUNT(*) FILTER (WHERE status IN ('passed','offer','failed','rejected')), 0) AS pass_rate,
                        COUNT(*) FILTER (WHERE scheduled_at >= NOW() - INTERVAL '1 day' * :days) AS recent_count
                    FROM interviews WHERE user_id = :uid AND deleted_at IS NULL
                """),
                {"uid": user_id, "days": days},
            )
            rate = rate_row.mappings().one()

            # 热门公司 top 5
            company_rows = await session.execute(
                text("""
                    SELECT c.name, COUNT(*) AS cnt
                    FROM interviews i JOIN companies c ON c.id = i.company_id
                    WHERE i.user_id = :uid AND i.deleted_at IS NULL
                    GROUP BY c.name ORDER BY cnt DESC LIMIT 5
                """),
                {"uid": user_id},
            )
            top_companies = [{"company": r["name"], "count": r["cnt"]} for r in company_rows.mappings().all()]

        logger.info("AnalyzeStatusTool", user_id=user_id)
        return {
            "status": "ok",
            "status_distribution": status_counts,
            "pass_rate_overall": round(float(rate["pass_rate"] or 0), 4),
            f"interviews_last_{days}_days": rate["recent_count"],
            "top_companies": top_companies,
        }

    @property
    def tool_schema(self) -> dict[str, Any]:
        return {
            "name": self.tool_name,
            "description": "Analyze the user's interview status distribution, pass rate, and top companies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "default": 30, "description": "Analysis window in days"},
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
