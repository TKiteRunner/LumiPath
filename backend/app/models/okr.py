"""
OKR 模型
表：okr_objectives / okr_key_results / daily_tasks
"""
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class OKRObjective(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, VersionMixin, Base):
    __tablename__ = "okr_objectives"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    quarter: Mapped[str] = mapped_column(String(8), nullable=False)   # 2026-Q2
    priority: Mapped[int] = mapped_column(SmallInteger, default=1)
    status: Mapped[str] = mapped_column(String(16), default="active")
    # active / paused / completed / abandoned
    progress: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0"))
    motivation: Mapped[str | None] = mapped_column(Text, nullable=True)
    success_picture: Mapped[str | None] = mapped_column(Text, nullable=True)
    vault_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

    key_results: Mapped[list["OKRKeyResult"]] = relationship(back_populates="objective", cascade="all, delete-orphan")


class OKRKeyResult(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, VersionMixin, Base):
    __tablename__ = "okr_key_results"

    objective_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("okr_objectives.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    metric: Mapped[str | None] = mapped_column(String(128), nullable=True)
    baseline: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    target: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    current: Mapped[Decimal] = mapped_column(Numeric, default=Decimal("0"))
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    weight: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("1.00"))
    progress: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0"))
    status: Mapped[str] = mapped_column(String(16), default="active")

    objective: Mapped["OKRObjective"] = relationship(back_populates="key_results")
    daily_tasks: Mapped[list["DailyTask"]] = relationship(back_populates="key_result")


class DailyTask(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "daily_tasks"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    kr_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("okr_key_results.id", ondelete="SET NULL"), nullable=True
    )
    task_date: Mapped[date] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)
    done_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    order_index: Mapped[int] = mapped_column(SmallInteger, default=0)

    key_result: Mapped["OKRKeyResult | None"] = relationship(back_populates="daily_tasks")
