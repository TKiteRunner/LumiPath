"""API v1 路由：OKR 规划。"""
import json
import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, require_permission
from app.db.session import get_async_session
from app.models.okr import OKRObjective, OKRKeyResult, DailyTask
from app.schemas.okr import (
    DailyTaskCreate, DailyTaskRead,
    KRCreate, KRRead, KRUpdate,
    ObjectiveCreate, ObjectiveRead,
)
from app.services.okr_service import okr_service

router = APIRouter(prefix="/okr", tags=["okr"])


# ── Objectives ────────────────────────────────────────────────────────────────
@router.get("/objectives", response_model=list[ObjectiveRead])
async def list_objectives(current_user: CurrentUser, quarter: str | None = None, db: AsyncSession = Depends(get_async_session)):
    stmt = (
        select(OKRObjective)
        .options(selectinload(OKRObjective.key_results))
        .where(OKRObjective.user_id == current_user.id, OKRObjective.deleted_at.is_(None))
    )
    if quarter:
        stmt = stmt.where(OKRObjective.quarter == quarter)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("/objectives", response_model=ObjectiveRead, status_code=201)
async def create_objective(
    body: ObjectiveCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
    _: None = require_permission("okr:write"),
):
    obj = await okr_service.create_objective(current_user.id, body, db)
    result = await db.execute(
        select(OKRObjective)
        .options(selectinload(OKRObjective.key_results))
        .where(OKRObjective.id == obj.id)
    )
    return result.scalar_one()


@router.delete("/objectives/{obj_id}", status_code=204)
async def delete_objective(obj_id: uuid.UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_async_session)):
    await okr_service.delete_objective(obj_id, current_user.id, db)


# ── Key Results ───────────────────────────────────────────────────────────────
@router.post("/objectives/{obj_id}/key-results", response_model=KRRead, status_code=201)
async def create_kr(
    obj_id: uuid.UUID,
    body: KRCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
):
    return await okr_service.create_kr(obj_id, current_user.id, body, db)


@router.patch("/key-results/{kr_id}", response_model=KRRead)
async def update_kr(kr_id: uuid.UUID, body: KRUpdate, current_user: CurrentUser, db: AsyncSession = Depends(get_async_session)):
    return await okr_service.update_kr(kr_id, body, current_user.id, db)


# ── Daily Tasks ───────────────────────────────────────────────────────────────
@router.get("/daily-tasks", response_model=list[DailyTaskRead])
async def list_daily_tasks(
    current_user: CurrentUser,
    task_date: date | None = None,
    db: AsyncSession = Depends(get_async_session),
):
    return await okr_service.list_daily_tasks(current_user.id, task_date, db)


@router.post("/daily-tasks", response_model=DailyTaskRead, status_code=201)
async def create_daily_task(body: DailyTaskCreate, current_user: CurrentUser, db: AsyncSession = Depends(get_async_session)):
    return await okr_service.create_daily_task(current_user.id, body, db)


@router.patch("/daily-tasks/{task_id}/done", response_model=DailyTaskRead)
async def mark_task_done(task_id: uuid.UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_async_session)):
    return await okr_service.mark_done(task_id, current_user.id, db)


# ── AI Task Suggestions ───────────────────────────────────────────────────────

_SUGGEST_PROMPT = """你是一位 OKR 执行教练。根据以下 OKR 信息，为用户生成今日（{date}）的任务清单。

## 当前 OKR 目标
{okr_block}

## 要求
- 输出 3~5 条具体可执行的任务
- 每条任务与某个 KR 关联
- 以 JSON 数组输出，每条结构：{{"title": "...", "kr_id": "..."}}
- 只输出 JSON 数组，不要有多余文字"""


@router.post("/objectives/{obj_id}/suggest_tasks", response_model=list[DailyTaskRead])
async def suggest_tasks(
    obj_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
):
    """用 LLM 基于当前 OKR 进度生成今日任务建议并写入 daily_tasks。"""
    # 1. 加载 Objective + KRs
    result = await db.execute(
        select(OKRObjective)
        .options(selectinload(OKRObjective.key_results))
        .where(OKRObjective.id == obj_id, OKRObjective.user_id == current_user.id, OKRObjective.deleted_at.is_(None))
    )
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Objective not found")

    active_krs = [kr for kr in obj.key_results if kr.deleted_at is None]
    if not active_krs:
        raise HTTPException(status_code=422, detail="No key results found for this objective")

    # 2. 获取用户 LLM 配置
    from app.agents.utils.llm_client import get_llm_config
    cfg = await get_llm_config(str(current_user.id), "okr")
    if not cfg:
        raise HTTPException(status_code=422, detail="请先在设置页配置 LLM API Key")

    # 3. 构建 OKR 上下文并调用 LLM
    okr_block = "\n".join(
        f"- KR: {kr.title}（当前 {kr.current} / 目标 {kr.target} {kr.unit or ''}，进度 {float(kr.progress)*100:.0f}%）[kr_id: {kr.id}]"
        for kr in active_krs
    )
    prompt = _SUGGEST_PROMPT.format(date=date.today().isoformat(), okr_block=okr_block)

    try:
        import litellm
        resp = await litellm.acompletion(
            **cfg.litellm_kwargs(),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.5,
        )
        raw = resp.choices[0].message.content.strip()
        # 提取 JSON 数组
        import re
        m = re.search(r"\[.*\]", raw, re.DOTALL)
        suggestions = json.loads(m.group()) if m else []
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM 调用失败：{exc}")

    # 4. 写入 daily_tasks
    now = datetime.now(timezone.utc)
    today = date.today()
    created = []
    for i, task in enumerate(suggestions[:5]):
        title = str(task.get("title", ""))[:255]
        if not title:
            continue
        kr_id_str = task.get("kr_id")
        kr_uuid = None
        if kr_id_str:
            try:
                kr_uuid = uuid.UUID(str(kr_id_str))
            except ValueError:
                pass
        new_task = DailyTask(
            id=uuid.uuid4(),
            user_id=current_user.id,
            kr_id=kr_uuid,
            task_date=today,
            title=title,
            description=task.get("description", ""),
            is_done=False,
            order_index=i,
            created_at=now,
            updated_at=now,
        )
        db.add(new_task)
        created.append(new_task)

    await db.commit()
    for t in created:
        await db.refresh(t)
    return created
