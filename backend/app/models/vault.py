"""
Vault 配置 & 冲突记录模型
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class VaultConfig(SoftDeleteMixin, TimestampMixin, Base):
    """每用户一条，user_id 作为主键。"""
    __tablename__ = "vault_configs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    vault_path: Mapped[str] = mapped_column(String(512), nullable=False)
    git_remote_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    git_credentials_encrypted: Mapped[bytes | None] = mapped_column(nullable=True)
    git_credential_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    # ssh_key / pat / basic
    auto_commit: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_push: Mapped[bool] = mapped_column(Boolean, default=False)
    commit_debounce_sec: Mapped[int] = mapped_column(Integer, default=10)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Conflict(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "conflicts"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("notes.id", ondelete="SET NULL"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    # file_vs_db / db_vs_file / git_merge
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    resolution: Mapped[str | None] = mapped_column(String(16), nullable=True)
    # auto_mtime / manual / deferred
    conflict_file: Mapped[str | None] = mapped_column(String(512), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
