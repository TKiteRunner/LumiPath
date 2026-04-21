"""
面试追踪模型
表：companies / interviews / interview_questions / interview_reviews
"""
import uuid
from datetime import datetime

from sqlalchemy import ARRAY, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class Company(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "companies"
    __table_args__ = (UniqueConstraint("name", "owner_id"),)

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    tier: Mapped[str | None] = mapped_column(String(8), nullable=True)   # T0 / T1 / T2
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(64), nullable=True)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    interviews: Mapped[list["Interview"]] = relationship(back_populates="company")


class Interview(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, VersionMixin, Base):
    __tablename__ = "interviews"
    __table_args__ = (
        CheckConstraint("round >= 1", name="ck_interview_round"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    role: Mapped[str] = mapped_column(String(128), nullable=False)
    round: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="scheduled")
    # scheduled / completed / passed / failed / offer / rejected / cancelled
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    interviewer: Mapped[str | None] = mapped_column(String(128), nullable=True)
    format: Mapped[str | None] = mapped_column(String(16), nullable=True)  # phone / video / onsite
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    vault_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(32)), default=list)

    company: Mapped["Company"] = relationship(back_populates="interviews")
    questions: Mapped[list["InterviewQuestion"]] = relationship(back_populates="interview", cascade="all, delete-orphan")
    review: Mapped["InterviewReview | None"] = relationship(back_populates="interview", uselist=False, cascade="all, delete-orphan")


class InterviewQuestion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "interview_questions"

    interview_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"))
    order_index: Mapped[int] = mapped_column(SmallInteger, default=0)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    my_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    standard_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    gap_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(32)), default=list)
    score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    interview: Mapped["Interview"] = relationship(back_populates="questions")


class InterviewReview(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "interview_reviews"

    interview_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"), unique=True
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    strengths: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    weaknesses: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    improvement_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    score_overall: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ai_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    version: Mapped[int] = mapped_column(default=0)

    interview: Mapped["Interview"] = relationship(back_populates="review")
