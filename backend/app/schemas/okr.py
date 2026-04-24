"""Pydantic v2 schemas for OKR."""
import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, model_validator


class ObjectiveCreate(BaseModel):
    title: str
    description: str | None = None
    quarter: str
    priority: int = 1
    motivation: str | None = None
    success_picture: str | None = None


class KRCreate(BaseModel):
    title: str
    metric: str | None = None
    baseline: Decimal | None = None
    target: Decimal | None = None
    unit: str | None = None
    weight: Decimal = Decimal("1.00")


class KRUpdate(BaseModel):
    current_value: Decimal | None = None
    current: Decimal | None = None
    status: str | None = None

    @model_validator(mode="after")
    def _merge_current(self):
        if self.current_value is not None and self.current is None:
            self.current = self.current_value
        return self


class KRRead(BaseModel):
    id: uuid.UUID
    title: str
    current_value: Decimal = Decimal("0")
    target_value: Decimal | None = None
    progress: Decimal = Decimal("0")
    status: str = "active"
    unit: str | None = None
    weight: Decimal = Decimal("1.00")

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def _map_fields(cls, data):
        if hasattr(data, "__dict__"):
            return {
                "id": data.id,
                "title": data.title,
                "current_value": data.current,
                "target_value": data.target,
                "progress": data.progress,
                "status": data.status,
                "unit": getattr(data, "unit", None),
                "weight": data.weight,
            }
        return data


class ObjectiveRead(BaseModel):
    id: uuid.UUID
    title: str
    quarter: str
    status: str
    progress: Decimal
    created_at: datetime
    key_results: list[KRRead] = []

    model_config = {"from_attributes": True}


class DailyTaskCreate(BaseModel):
    task_date: date
    title: str
    description: str | None = None
    kr_id: uuid.UUID | None = None


class DailyTaskRead(BaseModel):
    id: uuid.UUID
    task_date: date
    title: str
    completed: bool = False
    kr_id: uuid.UUID | None = None

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def _map_fields(cls, data):
        if hasattr(data, "__dict__"):
            return {
                "id": data.id,
                "task_date": data.task_date,
                "title": data.title,
                "completed": data.is_done,
                "kr_id": data.kr_id,
            }
        return data
