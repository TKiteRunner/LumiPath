"""API v1 路由：面试追踪。"""
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_permission
from app.db.session import get_async_session
from app.schemas.interview import (
    InterviewCreate, InterviewRead, InterviewUpdate,
    QuestionCreate, QuestionRead, QuestionUpdate,
)
from app.services.interview_service import interview_service

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.get("", response_model=list[InterviewRead])
async def list_interviews(current_user: CurrentUser, db: AsyncSession = Depends(get_async_session)):
    return await interview_service.list(current_user.id, db)


@router.post("", response_model=InterviewRead, status_code=201)
async def create_interview(
    body: InterviewCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
):
    return await interview_service.create(current_user.id, body, db)


@router.get("/{interview_id}", response_model=InterviewRead)
async def get_interview(interview_id: uuid.UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_async_session)):
    return await interview_service.get(interview_id, current_user.id, db)


@router.patch("/{interview_id}", response_model=InterviewRead)
async def update_interview(
    interview_id: uuid.UUID,
    body: InterviewUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
):
    return await interview_service.update(interview_id, body, current_user.id, db)


@router.delete("/{interview_id}", status_code=204)
async def delete_interview(interview_id: uuid.UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_async_session)):
    await interview_service.delete(interview_id, current_user.id, db)


# ── 题目 CRUD ─────────────────────────────────────────────────────────────────
@router.get("/{interview_id}/questions", response_model=list[QuestionRead])
async def list_questions(interview_id: uuid.UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_async_session)):
    return await interview_service.list_questions(interview_id, current_user.id, db)


@router.post("/{interview_id}/questions", response_model=QuestionRead, status_code=201)
async def add_question(
    interview_id: uuid.UUID,
    body: QuestionCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
):
    return await interview_service.add_question(interview_id, current_user.id, body, db)


@router.patch("/{interview_id}/questions/{question_id}", response_model=QuestionRead)
async def update_question(
    interview_id: uuid.UUID,
    question_id: uuid.UUID,
    body: QuestionUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
):
    return await interview_service.update_question(interview_id, question_id, current_user.id, body, db)


@router.delete("/{interview_id}/questions/{question_id}", status_code=204)
async def delete_question(
    interview_id: uuid.UUID,
    question_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
):
    await interview_service.delete_question(interview_id, question_id, current_user.id, db)


# ── AI 复盘（占位）────────────────────────────────────────────────────────────
@router.post("/{interview_id}/review", status_code=status.HTTP_202_ACCEPTED)
async def generate_review(
    interview_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
    _: None = require_permission("agent:invoke"),
):
    raise NotImplementedError
