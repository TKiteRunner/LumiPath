"""
ListInterviewsTool — 列出用户面试记录，支持状态过滤。
与 SearchQuestionsTool 区别：本 Tool 返回面试场次列表（不做全文检索），
主要供 MCP 客户端快速枚举、让 Agent 选择要分析的面试。
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

VALID_STATUSES = {
    "applied", "written_test", "first_interview",
    "second_interview", "hr_interview", "offer", "rejected",
}


@register_tool(name="list_interviews", version="1.0.0")
class ListInterviewsTool(BaseTool):

    async def execute(
        self,
        user_id: str,
        status: str = "",
        limit: int = 20,
        db: AsyncSession | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        async with _session(db) as session:
            conditions = ["i.user_id = :uid", "i.deleted_at IS NULL"]
            params: dict[str, Any] = {"uid": user_id, "limit": min(limit, 100)}

            if status and status in VALID_STATUSES:
                conditions.append("i.status = :status")
                params["status"] = status

            where = " AND ".join(conditions)
            rows = await session.execute(
                text(f"""
                    SELECT
                        i.id,
                        i.position,
                        i.status,
                        i.round,
                        TO_CHAR(i.scheduled_at, 'YYYY-MM-DD') AS interview_date,
                        i.created_at,
                        c.name AS company_name,
                        (SELECT COUNT(*) FROM interview_questions iq
                         WHERE iq.interview_id = i.id) AS question_count
                    FROM interviews i
                    LEFT JOIN companies c ON c.id = i.company_id
                    WHERE {where}
                    ORDER BY i.created_at DESC
                    LIMIT :limit
                """),
                params,
            )
            interviews = [dict(r) for r in rows.mappings().all()]

        logger.info("ListInterviewsTool", user_id=user_id, status=status, count=len(interviews))
        return {"status": "ok", "interviews": interviews, "count": len(interviews)}

    @property
    def tool_schema(self) -> dict[str, Any]:
        return {
            "name": self.tool_name,
            "description": (
                "List the user's interview records. "
                "Optionally filter by status: applied, written_test, first_interview, "
                "second_interview, hr_interview, offer, rejected. "
                "Returns company, position, round, date, and question count."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID"},
                    "status": {
                        "type": "string",
                        "enum": list(VALID_STATUSES),
                        "description": "Filter by interview status. Omit to return all.",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 20,
                        "description": "Maximum number of records to return (max 100).",
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
