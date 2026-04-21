"""
面试服务骨架：CRUD + 状态机
"""
from __future__ import annotations

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.interview import Interview
from app.schemas.interview import InterviewCreate, InterviewUpdate

# 面试状态机合法转换
_VALID_TRANSITIONS: dict[str, set[str]] = {
    "scheduled":  {"completed", "cancelled"},
    "completed":  {"passed", "failed", "offer", "rejected"},
    "passed":     {"offer", "rejected"},
    "failed":     set(),
    "offer":      {"rejected"},
    "rejected":   set(),
    "cancelled":  set(),
}


class InterviewService:

    async def list(self, user_id: uuid.UUID, db: AsyncSession) -> list[Interview]:
        result = await db.execute(
            select(Interview).where(Interview.user_id == user_id, Interview.deleted_at.is_(None))
        )
        return list(result.scalars().all())

    async def get(self, interview_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> Interview:
        return await self._get_owned(interview_id, user_id, db)

    async def create(self, user_id: uuid.UUID, body: InterviewCreate, db: AsyncSession) -> Interview:
        interview = Interview(user_id=user_id, **body.model_dump())
        db.add(interview)
        await db.flush()
        return interview

    async def update(
        self, interview_id: uuid.UUID, body: InterviewUpdate, user_id: uuid.UUID, db: AsyncSession
    ) -> Interview:
        interview = await self._get_owned(interview_id, user_id, db)
        data = body.model_dump(exclude_none=True)

        if "status" in data:
            new_status = data["status"]
            if new_status not in _VALID_TRANSITIONS.get(interview.status, set()):
                raise NotFoundError(f"Invalid status transition: {interview.status} → {new_status}")
            interview.status = new_status

        for k, v in data.items():
            if k != "status":
                setattr(interview, k, v)

        interview.version += 1
        await db.flush()
        return interview

    async def delete(self, interview_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> None:
        interview = await self._get_owned(interview_id, user_id, db)
        from datetime import datetime, timezone
        interview.deleted_at = datetime.now(timezone.utc)
        await db.flush()

    # ── helpers ──────────────────────────────────────────────────────────────
    @staticmethod
    async def _get_owned(interview_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> Interview:
        result = await db.execute(
            select(Interview).where(Interview.id == interview_id, Interview.deleted_at.is_(None))
        )
        interview = result.scalar_one_or_none()
        if not interview:
            raise NotFoundError("Interview not found")
        if interview.user_id != user_id:
            raise ForbiddenError("Not the owner of this interview")
        return interview


interview_service = InterviewService()
