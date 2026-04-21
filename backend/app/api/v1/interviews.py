"""API v1 路由：面试追踪。"""
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_permission
from app.db.session import get_async_session
from app.schemas.interview import (
    InterviewCreate, InterviewRead, InterviewUpdate,
    QuestionCreate, QuestionRead, ReviewRead,
)

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.get("", response_model=list[InterviewRead])
async def list_interviews(current_user: CurrentUser, db: AsyncSession = Depends(get_async_session)):
    # TODO: interview_service.list(current_user.id, db)
    raise NotImplementedError


@router.post("", response_model=InterviewRead, status_code=201)
async def create_interview(
    body: InterviewCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
    _: None = require_permission("interview:write"),
):
    # TODO: interview_service.create(current_user.id, body, db)
    raise NotImplementedError


@router.get("/{interview_id}", response_model=InterviewRead)
async def get_interview(interview_id: uuid.UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_async_session)):
    # TODO: interview_service.get(interview_id, current_user.id, db)
    raise NotImplementedError


@router.patch("/{interview_id}", response_model=InterviewRead)
async def update_interview(
    interview_id: uuid.UUID,
    body: InterviewUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
):
    # TODO: interview_service.update(interview_id, body, current_user.id, db)
    raise NotImplementedError


@router.delete("/{interview_id}", status_code=204)
async def delete_interview(interview_id: uuid.UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_async_session)):
    # TODO: interview_service.delete(interview_id, current_user.id, db)
    raise NotImplementedError


# ── 题目 CRUD ─────────────────────────────────────────────────────────────────
@router.post("/{interview_id}/questions", response_model=QuestionRead, status_code=201)
async def add_question(
    interview_id: uuid.UUID,
    body: QuestionCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
):
    # TODO
    raise NotImplementedError


# ── AI 复盘（异步长任务）────────────────────────────────────────────────────
@router.post("/{interview_id}/review", status_code=status.HTTP_202_ACCEPTED)
async def generate_review(
    interview_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
    _: None = require_permission("agent:invoke"),
):
    """
    触发 Interview Agent 生成复盘报告，立即返回 task_id。
    前端通过 WS /ws/tasks/{task_id} 订阅进度。
    """
    # TODO:
    #   1. 生成 task_id + 写 task_idempotency
    #   2. publish to RabbitMQ agent_long 队列
    #   3. return {"task_id": task_id}
    raise NotImplementedError
