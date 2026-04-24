"""Pydantic v2 schemas for notes."""
import uuid
from datetime import date, datetime

from pydantic import BaseModel


class DailyNoteUpsert(BaseModel):
    """PUT /notes/daily/{date} 的请求体。"""
    content: str          # 完整 Markdown 内容（含 frontmatter）


class NoteRead(BaseModel):
    id: uuid.UUID
    path: str
    type: str
    title: str | None
    note_date: date | None
    content_preview: str | None
    word_count: int
    is_private: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class NoteCreate(BaseModel):
    path: str
    type: str
    content: str


class NoteWithContent(NoteRead):
    content: str


class NoteListItem(BaseModel):
    id: uuid.UUID
    path: str
    title: str | None
    note_date: date | None
    tags: list[str] = []
    word_count: int
    model_config = {"from_attributes": True}
