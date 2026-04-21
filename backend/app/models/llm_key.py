"""
LLM API Key 相关模型
表：user_llm_keys / agent_llm_assignments / user_llm_key_usage
"""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


_AGENT_NAMES = ("supervisor", "interview", "okr", "notes", "memory")


class UserLLMKey(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_llm_keys"
    __table_args__ = (UniqueConstraint("user_id", "provider", "key_alias"),)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    key_alias: Mapped[str] = mapped_column(String(64), nullable=False)
    api_key_encrypted: Mapped[bytes] = mapped_column(nullable=False)
    key_last4: Mapped[str] = mapped_column(String(4), nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    default_model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    monthly_budget_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    monthly_used_usd: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=Decimal("0"))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="llm_keys")  # type: ignore[name-defined]
    assignments: Mapped[list["AgentLLMAssignment"]] = relationship(back_populates="key", cascade="all, delete-orphan")


class AgentLLMAssignment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agent_llm_assignments"
    __table_args__ = (
        UniqueConstraint("user_id", "agent_name"),
        CheckConstraint(f"agent_name IN {_AGENT_NAMES}", name="ck_agent_name"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    agent_name: Mapped[str] = mapped_column(String(32), nullable=False)
    key_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_llm_keys.id", ondelete="CASCADE"))

    key: Mapped["UserLLMKey"] = relationship(back_populates="assignments")


class UserLLMKeyUsage(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "user_llm_key_usage"

    key_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_llm_keys.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(nullable=True)
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
