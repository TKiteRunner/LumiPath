"""
面试服务：CRUD + 自动公司管理 + 问题记录
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.interview import Company, Interview, InterviewQuestion
from app.schemas.interview import InterviewCreate, InterviewUpdate, QuestionCreate, QuestionUpdate


class InterviewService:

    async def list(self, user_id: uuid.UUID, db: AsyncSession) -> list[Interview]:
        result = await db.execute(
            select(Interview)
            .options(selectinload(Interview.company))
            .where(Interview.user_id == user_id, Interview.deleted_at.is_(None))
            .order_by(Interview.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, interview_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> Interview:
        return await self._get_owned(interview_id, user_id, db)

    async def create(self, user_id: uuid.UUID, body: InterviewCreate, db: AsyncSession) -> Interview:
        company = await self._get_or_create_company(body.company_name, user_id, db)
        interview = Interview(
            user_id=user_id,
            company_id=company.id,
            role=body.position,
            round=body.round,
            status=body.status,
            scheduled_at=body.interview_date,
            notes=body.notes,
        )
        db.add(interview)
        await db.flush()
        await db.refresh(interview, ["company"])
        return interview

    async def update(
        self, interview_id: uuid.UUID, body: InterviewUpdate, user_id: uuid.UUID, db: AsyncSession
    ) -> Interview:
        interview = await self._get_owned(interview_id, user_id, db)
        if body.status is not None:
            interview.status = body.status
        if body.notes is not None:
            interview.notes = body.notes
        if body.interview_date is not None:
            interview.scheduled_at = body.interview_date
        interview.version += 1
        await db.flush()
        return interview

    async def delete(self, interview_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> None:
        interview = await self._get_owned(interview_id, user_id, db)
        interview.deleted_at = datetime.now(timezone.utc)
        await db.flush()

    # ── 问题 CRUD ─────────────────────────────────────────────────────────────
    async def list_questions(self, interview_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> list[InterviewQuestion]:
        await self._get_owned(interview_id, user_id, db)
        result = await db.execute(
            select(InterviewQuestion)
            .where(InterviewQuestion.interview_id == interview_id)
            .order_by(InterviewQuestion.category, InterviewQuestion.order_index)
        )
        return list(result.scalars().all())

    async def add_question(self, interview_id: uuid.UUID, user_id: uuid.UUID, body: QuestionCreate, db: AsyncSession) -> InterviewQuestion:
        await self._get_owned(interview_id, user_id, db)
        count = await db.scalar(
            select(func.count(InterviewQuestion.id))
            .where(InterviewQuestion.interview_id == interview_id, InterviewQuestion.category == body.category)
        ) or 0
        q = InterviewQuestion(
            interview_id=interview_id,
            order_index=count,
            question_text=body.question_text,
            my_answer=body.my_answer,
            difficulty=body.difficulty,
            category=body.category,
            tags=body.tags,
        )
        db.add(q)
        await db.flush()
        await db.refresh(q)
        return q

    async def update_question(self, interview_id: uuid.UUID, question_id: uuid.UUID, user_id: uuid.UUID, body: QuestionUpdate, db: AsyncSession) -> InterviewQuestion:
        await self._get_owned(interview_id, user_id, db)
        q = await db.get(InterviewQuestion, question_id)
        if not q or q.interview_id != interview_id:
            raise NotFoundError("Question not found")
        for k, v in body.model_dump(exclude_none=True).items():
            setattr(q, k, v)
        await db.flush()
        await db.refresh(q)
        return q

    async def delete_question(self, interview_id: uuid.UUID, question_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> None:
        await self._get_owned(interview_id, user_id, db)
        q = await db.get(InterviewQuestion, question_id)
        if not q or q.interview_id != interview_id:
            raise NotFoundError("Question not found")
        await db.delete(q)
        await db.flush()

    # ── helpers ──────────────────────────────────────────────────────────────
    @staticmethod
    async def _get_owned(interview_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> Interview:
        result = await db.execute(
            select(Interview)
            .options(selectinload(Interview.company))
            .where(Interview.id == interview_id, Interview.deleted_at.is_(None))
        )
        interview = result.scalar_one_or_none()
        if not interview:
            raise NotFoundError("Interview not found")
        if interview.user_id != user_id:
            raise ForbiddenError("Not the owner of this interview")
        return interview

    @staticmethod
    async def _get_or_create_company(name: str, user_id: uuid.UUID, db: AsyncSession) -> Company:
        result = await db.execute(
            select(Company).where(Company.name == name, Company.owner_id == user_id)
        )
        company = result.scalar_one_or_none()
        if not company:
            slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            slug = f"{slug}-{str(user_id)[:8]}"
            company = Company(name=name, slug=slug, owner_id=user_id)
            db.add(company)
            await db.flush()
        return company


interview_service = InterviewService()
