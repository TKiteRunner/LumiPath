"""Pydantic v2 schemas for OKR."""
import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class ObjectiveCreate(BaseModel):
    title: str
    description: str | None = None
    quarter: str
    priority: int = 1
    motivation: str | None = None
    success_picture: str | None = None


class ObjectiveRead(BaseModel):
    id: uuid.UUID
    title: str
    quarter: str
    status: str
    progress: Decimal
    created_at: datetime
    model_config = {"from_attributes": True}


class KRCreate(BaseModel):
    title: str
    metric: str | None = None
    baseline: Decimal | None = None
    target: Decimal | None = None
    unit: str | None = None
    weight: Decimal = Decimal("1.00")


class KRRead(BaseModel):
    id: uuid.UUID
    title: str
    current: Decimal
    target: Decimal | None
    progress: Decimal
    status: str
    model_config = {"from_attributes": True}


class KRUpdate(BaseModel):
    current: Decimal | None = None
    status: str | None = None


class DailyTaskCreate(BaseModel):
    task_date: date
    title: str
    description: str | None = None
    kr_id: uuid.UUID | None = None


class DailyTaskRead(BaseModel):
    id: uuid.UUID
    task_date: date
    title: str
    is_done: bool
    kr_id: uuid.UUID | None
    model_config = {"from_attributes": True}
