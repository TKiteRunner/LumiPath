"""
笔记 Vault 模型
表：notes / note_tags / note_links / note_embeddings
"""
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class Note(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, VersionMixin, Base):
    __tablename__ = "notes"
    __table_args__ = (UniqueConstraint("user_id", "path"),)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    # daily/weekly/monthly/interview/okr/concept/company/free
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    frontmatter: Mapped[dict] = mapped_column(JSONB, default=dict)
    content_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)   # sha256
    file_mtime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False)
    interview_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="SET NULL"), nullable=True
    )
    kr_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("okr_key_results.id", ondelete="SET NULL"), nullable=True
    )

    tags: Mapped[list["NoteTag"]] = relationship(back_populates="note", cascade="all, delete-orphan")
    source_links: Mapped[list["NoteLink"]] = relationship(
        back_populates="source_note", foreign_keys="NoteLink.source_note_id", cascade="all, delete-orphan"
    )
    embeddings: Mapped[list["NoteEmbedding"]] = relationship(back_populates="note", cascade="all, delete-orphan")


class NoteTag(Base):
    __tablename__ = "note_tags"

    note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True
    )
    tag: Mapped[str] = mapped_column(String(64), primary_key=True)

    note: Mapped["Note"] = relationship(back_populates="tags")


class NoteLink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "note_links"

    source_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE")
    )
    target_note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("notes.id", ondelete="SET NULL"), nullable=True
    )
    target_slug: Mapped[str | None] = mapped_column(String(255), nullable=True)
    anchor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_text: Mapped[str | None] = mapped_column(String(255), nullable=True)

    source_note: Mapped["Note"] = relationship(back_populates="source_links", foreign_keys=[source_note_id])


class NoteEmbedding(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    笔记的向量嵌入（多模型多维度并存）。
    pgvector 的 Vector 类型在 alembic migration 中用 `vector(n)` 原生类型定义；
    ORM 层用 Text 占位，实际 DDL 由 migration 管理。
    """
    __tablename__ = "note_embeddings"
    __table_args__ = (UniqueConstraint("note_id", "chunk_index", "model_name"),)

    note_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"))
    chunk_index: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    # 向量列由 Alembic migration 使用 vector(n) 类型创建，ORM 暂不声明避免驱动依赖

    note: Mapped["Note"] = relationship(back_populates="embeddings")
