"""API v1 路由：笔记 Vault。"""
import uuid
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_permission
from app.db.session import get_async_session
from app.schemas.note import DailyNoteUpsert, NoteListItem, NoteRead

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("", response_model=list[NoteListItem])
async def list_notes(
    current_user: CurrentUser,
    type: str | None = None,
    tag: str | None = None,
    db: AsyncSession = Depends(get_async_session),
):
    """列出用户笔记（按类型/标签过滤）。"""
    # TODO: notes_service.list(current_user.id, type, tag, db)
    raise NotImplementedError


@router.get("/{note_id}", response_model=NoteRead)
async def get_note(note_id: uuid.UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_async_session)):
    # TODO: notes_service.get(note_id, current_user.id, db)
    raise NotImplementedError


@router.put(
    "/daily/{note_date}",
    response_model=NoteRead,
    dependencies=[require_permission("note:write")],
)
async def upsert_daily_note(
    note_date: date,
    body: DailyNoteUpsert,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
):
    """
    保存每日笔记（幂等）。
    流程：写 vault .md → upsert DB → 发 MQ embedding + vault_sync 事件。
    """
    # TODO: notes_service.upsert_daily(current_user.id, note_date, body.content, db)
    raise NotImplementedError


@router.delete("/{note_id}", status_code=204)
async def delete_note(note_id: uuid.UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_async_session)):
    # TODO: notes_service.delete(note_id, current_user.id, db)
    raise NotImplementedError
