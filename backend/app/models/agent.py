"""
Agent 会话 & 消息模型
"""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AgentSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agent_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    thread_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    context_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # interview / okr / note / free
    context_ref: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="active")
    model_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    llm_key_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_llm_keys.id", ondelete="SET NULL"), nullable=True
    )
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=Decimal("0"))

    messages: Mapped[list["AgentMessage"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class AgentMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agent_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agent_sessions.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    # system / user / assistant / tool
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    tool_calls: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tool_call_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tokens: Mapped[int] = mapped_column(Integer, default=0)
    node_name: Mapped[str | None] = mapped_column(String(64), nullable=True)

    session: Mapped["AgentSession"] = relationship(back_populates="messages")
