"""Pydantic v2 schemas for agent chat."""
import uuid
from datetime import datetime

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None     # None → 创建新 session
    context_type: str | None = None   # interview / okr / note / free
    context_ref: uuid.UUID | None = None


class ChatResponse(BaseModel):
    session_id: str
    task_id: uuid.UUID
    status: str = "queued"


class TaskStatus(BaseModel):
    task_id: uuid.UUID
    status: str    # queued / running / done / failed
    stage: str | None = None
    result: dict | None = None
    created_at: datetime
