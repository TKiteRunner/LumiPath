"""Pydantic v2 schemas for users and LLM keys."""
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr


class UserRead(BaseModel):
    id: uuid.UUID
    email: str | None
    display_name: str
    avatar_url: str | None
    locale: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    display_name: str | None = None
    avatar_url: str | None = None
    locale: str | None = None


class LLMKeyCreate(BaseModel):
    provider: str
    key_alias: str
    api_key: str          # 明文，后端加密后存储
    base_url: str | None = None
    default_model: str | None = None
    is_default: bool = False
    monthly_budget_usd: Decimal | None = None


class LLMKeyRead(BaseModel):
    id: uuid.UUID
    provider: str
    key_alias: str
    key_last4: str
    default_model: str | None
    is_active: bool
    is_default: bool
    monthly_budget_usd: Decimal | None
    monthly_used_usd: Decimal
    last_used_at: datetime | None

    model_config = {"from_attributes": True}


class AgentAssignmentCreate(BaseModel):
    agent_name: str   # supervisor / interview / okr / notes / memory
    key_id: uuid.UUID


class AgentAssignmentRead(BaseModel):
    id: uuid.UUID
    agent_name: str
    key_id: uuid.UUID

    model_config = {"from_attributes": True}
