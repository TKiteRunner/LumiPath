"""Pydantic v2 schemas for interviews."""
import uuid
from datetime import datetime

from pydantic import BaseModel, model_validator


class InterviewCreate(BaseModel):
    company_name: str
    position: str
    round: int = 1
    status: str = "applied"
    interview_date: datetime | None = None
    notes: str | None = None


class InterviewRead(BaseModel):
    id: uuid.UUID
    company_name: str = ""
    position: str = ""
    round: int
    status: str
    interview_date: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def _flatten(cls, data):
        if hasattr(data, "__dict__"):
            d = {
                "id": data.id,
                "position": getattr(data, "role", ""),
                "round": data.round,
                "status": data.status,
                "interview_date": getattr(data, "scheduled_at", None),
                "notes": getattr(data, "notes", None),
                "created_at": data.created_at,
                "updated_at": data.updated_at,
                "company_name": "",
            }
            if hasattr(data, "company") and data.company:
                d["company_name"] = data.company.name
            return d
        return data


class InterviewUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None
    interview_date: datetime | None = None


class QuestionCreate(BaseModel):
    question_text: str
    my_answer: str | None = None
    difficulty: int | None = None
    category: str | None = None  # used as stage key: written_test / first_interview / etc.
    tags: list[str] = []


class QuestionUpdate(BaseModel):
    question_text: str | None = None
    my_answer: str | None = None
    difficulty: int | None = None
    score: int | None = None


class QuestionRead(BaseModel):
    id: uuid.UUID
    order_index: int
    question_text: str
    my_answer: str | None
    standard_answer: str | None
    gap_analysis: str | None
    difficulty: int | None
    category: str | None
    score: int | None
    model_config = {"from_attributes": True}


class ReviewRead(BaseModel):
    id: uuid.UUID
    summary: str
    strengths: list[str] | None
    weaknesses: list[str] | None
    improvement_plan: str | None
    score_overall: int | None
    ai_model: str | None
    generated_at: datetime
    model_config = {"from_attributes": True}
