"""API v1 路由：笔记 Vault。"""
import uuid
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_permission
from app.db.session import get_async_session
from app.schemas.note import DailyNoteUpsert, NoteListItem, NoteRead
from app.services import notes_service
from app.workers.embedding_worker import process_note_embedding
from app.workers.vault_watcher import sync_vault

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("", response_model=list[NoteRead])
async def list_notes(
    current_user: CurrentUser,
    type: str | None = None,
    tag: str | None = None,
    db: AsyncSession = Depends(get_async_session),
):
    """列出用户笔记（按类型/标签过滤）。"""
    return await notes_service.list_notes(current_user.id, db, type=type, tag=tag)


@router.get("/{note_id}", response_model=NoteRead)
async def get_note(
    note_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
):
    """获取单条笔记元数据。"""
    return await notes_service.get_note(note_id, current_user.id, db)


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
    保存每日笔记（幂等 upsert）。
    流程：写 vault .md → upsert DB → 异步触发 embedding + vault_sync。
    """
    note = await notes_service.upsert_daily_note(current_user.id, note_date, body.content, db)

    # 异步触发 embedding（非阻塞，Step 3 接入真实向量模型）
    process_note_embedding.apply_async(
        args=[str(note.id), body.content],
        queue="embedding",
    )
    # 异步触发 Git 提交
    sync_vault.apply_async(
        args=[str(current_user.id), f"update daily note {note_date}"],
        queue="vault_sync",
    )
    return note


@router.delete("/{note_id}", status_code=204)
async def delete_note(
    note_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
):
    """软删除笔记。"""
    await notes_service.delete_note(note_id, current_user.id, db)
