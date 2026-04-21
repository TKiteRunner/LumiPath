"""
7层 Cognitive Memory 对应的 PG 模型
表：memory_long_term / memory_long_term_history / memory_summaries /
    memory_episodes / memory_procedures / tools_registry
"""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class MemoryLongTerm(VersionMixin, Base):
    """长期画像，user_id 为主键。"""
    __tablename__ = "memory_long_term"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    profile: Mapped[dict] = mapped_column(JSONB, default=dict)
    ability_model: Mapped[dict] = mapped_column(JSONB, default=dict)
    preferences: Mapped[dict] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MemoryLongTermHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "memory_long_term_history"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    diff: Mapped[dict] = mapped_column(JSONB, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class MemorySummary(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """压缩摘要，含多模型向量列（由 migration 实际创建 vector 类型）。"""
    __tablename__ = "memory_summaries"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # conversation / interview / weekly / monthly
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tokens_saved: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 向量列由 migration 创建，ORM 层不声明


class MemoryEpisode(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """情景记忆——一次有边界的事件快照。"""
    __tablename__ = "memory_episodes"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    context: Mapped[dict] = mapped_column(JSONB, default=dict)
    narrative: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    linked_notes: Mapped[list[str]] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list)
    linked_interview_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="SET NULL"), nullable=True
    )
    importance: Mapped[int] = mapped_column(SmallInteger, default=5)
    # 向量列由 migration 创建


class MemoryProcedure(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """程序记忆——Skill 执行日志。"""
    __tablename__ = "memory_procedures"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    skill_name: Mapped[str] = mapped_column(String(64), nullable=False)
    skill_version: Mapped[str | None] = mapped_column(String(16), nullable=True)
    input: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    review: Mapped[str | None] = mapped_column(Text, nullable=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_sessions.id", ondelete="SET NULL"), nullable=True
    )
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SkillsRegistry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Skill 元数据注册表。"""
    __tablename__ = "skills_registry"

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[str] = mapped_column(String(16), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_schema: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_schema: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    requires_llm: Mapped[bool] = mapped_column(Boolean, default=True)
    avg_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
