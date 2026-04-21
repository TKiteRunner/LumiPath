"""Pydantic v2 schemas for interviews."""
import uuid
from datetime import datetime

from pydantic import BaseModel


class CompanyRead(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    tier: str | None
    model_config = {"from_attributes": True}


class InterviewCreate(BaseModel):
    company_id: uuid.UUID
    role: str
    round: int
    scheduled_at: datetime | None = None
    format: str | None = None
    notes: str | None = None


class InterviewRead(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    role: str
    round: int
    status: str
    scheduled_at: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}


class InterviewUpdate(BaseModel):
    status: str | None = None
    duration_min: int | None = None
    notes: str | None = None


class QuestionCreate(BaseModel):
    question_text: str
    my_answer: str | None = None
    difficulty: int | None = None
    category: str | None = None
    tags: list[str] = []


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
