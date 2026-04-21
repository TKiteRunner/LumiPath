"""
OKR 服务骨架：CRUD + 进度衍生计算
"""
from __future__ import annotations

import uuid
from decimal import Decimal
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.okr import OKRObjective, OKRKeyResult, DailyTask
from app.schemas.okr import KRUpdate, ObjectiveCreate, KRCreate, DailyTaskCreate


class OKRService:

    # ── Objectives ────────────────────────────────────────────────────────────
    async def list_objectives(
        self, user_id: uuid.UUID, quarter: str | None, db: AsyncSession
    ) -> list[OKRObjective]:
        stmt = select(OKRObjective).where(
            OKRObjective.user_id == user_id, OKRObjective.deleted_at.is_(None)
        )
        if quarter:
            stmt = stmt.where(OKRObjective.quarter == quarter)
        return list((await db.execute(stmt)).scalars().all())

    async def create_objective(
        self, user_id: uuid.UUID, body: ObjectiveCreate, db: AsyncSession
    ) -> OKRObjective:
        obj = OKRObjective(user_id=user_id, **body.model_dump())
        db.add(obj)
        await db.flush()
        return obj

    async def delete_objective(
        self, obj_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
    ) -> None:
        obj = await self._get_owned_obj(obj_id, user_id, db)
        from datetime import datetime, timezone
        obj.deleted_at = datetime.now(timezone.utc)
        await db.flush()

    # ── Key Results ───────────────────────────────────────────────────────────
    async def create_kr(
        self, obj_id: uuid.UUID, user_id: uuid.UUID, body: KRCreate, db: AsyncSession
    ) -> OKRKeyResult:
        await self._get_owned_obj(obj_id, user_id, db)  # 校验所有权
        kr = OKRKeyResult(objective_id=obj_id, **body.model_dump())
        db.add(kr)
        await db.flush()
        return kr

    async def update_kr(
        self, kr_id: uuid.UUID, body: KRUpdate, user_id: uuid.UUID, db: AsyncSession
    ) -> OKRKeyResult:
        kr = await self._get_owned_kr(kr_id, user_id, db)
        if body.current is not None:
            kr.current = body.current
            kr.progress = self._calc_kr_progress(kr)
        if body.status is not None:
            kr.status = body.status
        kr.version += 1
        await db.flush()
        # 重新计算 Objective progress
        await self._recalculate_obj_progress(kr.objective_id, db)
        return kr

    # ── Daily Tasks ───────────────────────────────────────────────────────────
    async def list_daily_tasks(
        self, user_id: uuid.UUID, task_date, db: AsyncSession
    ) -> list[DailyTask]:
        stmt = select(DailyTask).where(DailyTask.user_id == user_id)
        if task_date:
            stmt = stmt.where(DailyTask.task_date == task_date)
        return list((await db.execute(stmt)).scalars().all())

    async def create_daily_task(
        self, user_id: uuid.UUID, body: DailyTaskCreate, db: AsyncSession
    ) -> DailyTask:
        task = DailyTask(user_id=user_id, **body.model_dump())
        db.add(task)
        await db.flush()
        return task

    async def mark_done(self, task_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> DailyTask:
        result = await db.execute(
            select(DailyTask).where(DailyTask.id == task_id, DailyTask.user_id == user_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            raise NotFoundError("Task not found")
        from datetime import datetime, timezone
        task.is_done = True
        task.done_at = datetime.now(timezone.utc)
        await db.flush()
        return task

    # ── helpers ──────────────────────────────────────────────────────────────
    @staticmethod
    def _calc_kr_progress(kr: OKRKeyResult) -> Decimal:
        """线性进度：(current - baseline) / (target - baseline)，裁剪到 [0, 1]。"""
        baseline = kr.baseline or Decimal("0")
        target = kr.target or Decimal("1")
        if target == baseline:
            return Decimal("1") if kr.current >= target else Decimal("0")
        raw = (kr.current - baseline) / (target - baseline)
        return max(Decimal("0"), min(Decimal("1"), raw))

    @staticmethod
    async def _recalculate_obj_progress(obj_id: uuid.UUID, db: AsyncSession) -> None:
        """加权平均所有 KR 进度 → 更新 Objective.progress。"""
        result = await db.execute(
            select(OKRKeyResult).where(
                OKRKeyResult.objective_id == obj_id, OKRKeyResult.deleted_at.is_(None)
            )
        )
        krs = result.scalars().all()
        if not krs:
            return
        total_weight = sum(kr.weight for kr in krs)
        if total_weight == 0:
            return
        weighted_sum = sum(kr.progress * kr.weight for kr in krs)
        new_progress = weighted_sum / total_weight
        await db.execute(
            update(OKRObjective).where(OKRObjective.id == obj_id).values(progress=new_progress)
        )

    @staticmethod
    async def _get_owned_obj(obj_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> OKRObjective:
        result = await db.execute(
            select(OKRObjective).where(OKRObjective.id == obj_id, OKRObjective.deleted_at.is_(None))
        )
        obj = result.scalar_one_or_none()
        if not obj:
            raise NotFoundError("Objective not found")
        if obj.user_id != user_id:
            raise ForbiddenError("Not the owner")
        return obj

    @staticmethod
    async def _get_owned_kr(kr_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> OKRKeyResult:
        from sqlalchemy import join
        stmt = (
            select(OKRKeyResult)
            .join(OKRObjective, OKRObjective.id == OKRKeyResult.objective_id)
            .where(OKRKeyResult.id == kr_id, OKRObjective.user_id == user_id, OKRKeyResult.deleted_at.is_(None))
        )
        kr = (await db.execute(stmt)).scalar_one_or_none()
        if not kr:
            raise NotFoundError("Key result not found or not owned")
        return kr


okr_service = OKRService()
