"""API v1 路由：OKR 规划。"""
import uuid
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_permission
from app.db.session import get_async_session
from app.schemas.okr import (
    DailyTaskCreate, DailyTaskRead,
    KRCreate, KRRead, KRUpdate,
    ObjectiveCreate, ObjectiveRead,
)

router = APIRouter(prefix="/okr", tags=["okr"])


# ── Objectives ────────────────────────────────────────────────────────────────
@router.get("/objectives", response_model=list[ObjectiveRead])
async def list_objectives(current_user: CurrentUser, quarter: str | None = None, db: AsyncSession = Depends(get_async_session)):
    # TODO: okr_service.list_objectives(current_user.id, quarter, db)
    raise NotImplementedError


@router.post("/objectives", response_model=ObjectiveRead, status_code=201)
async def create_objective(
    body: ObjectiveCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
    _: None = require_permission("okr:write"),
):
    # TODO
    raise NotImplementedError


@router.delete("/objectives/{obj_id}", status_code=204)
async def delete_objective(obj_id: uuid.UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_async_session)):
    # TODO
    raise NotImplementedError


# ── Key Results ───────────────────────────────────────────────────────────────
@router.post("/objectives/{obj_id}/key-results", response_model=KRRead, status_code=201)
async def create_kr(
    obj_id: uuid.UUID,
    body: KRCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
):
    # TODO
    raise NotImplementedError


@router.patch("/key-results/{kr_id}", response_model=KRRead)
async def update_kr(kr_id: uuid.UUID, body: KRUpdate, current_user: CurrentUser, db: AsyncSession = Depends(get_async_session)):
    # TODO: okr_service.update_kr(kr_id, body, current_user.id, db) → recalculate objective progress
    raise NotImplementedError


# ── Daily Tasks ───────────────────────────────────────────────────────────────
@router.get("/daily-tasks", response_model=list[DailyTaskRead])
async def list_daily_tasks(
    current_user: CurrentUser,
    task_date: date | None = None,
    db: AsyncSession = Depends(get_async_session),
):
    # TODO
    raise NotImplementedError


@router.post("/daily-tasks", response_model=DailyTaskRead, status_code=201)
async def create_daily_task(body: DailyTaskCreate, current_user: CurrentUser, db: AsyncSession = Depends(get_async_session)):
    # TODO
    raise NotImplementedError


@router.patch("/daily-tasks/{task_id}/done", response_model=DailyTaskRead)
async def mark_task_done(task_id: uuid.UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_async_session)):
    # TODO
    raise NotImplementedError
