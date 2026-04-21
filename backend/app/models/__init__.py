"""
models package：统一导出所有 ORM 模型，确保 Alembic 能发现所有 metadata。
"""
from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin
from app.models.user import User, OAuthAccount, Role, Permission, UserRole, RolePermission
from app.models.llm_key import UserLLMKey, AgentLLMAssignment, UserLLMKeyUsage
from app.models.interview import Company, Interview, InterviewQuestion, InterviewReview
from app.models.okr import OKRObjective, OKRKeyResult, DailyTask
from app.models.note import Note, NoteTag, NoteLink, NoteEmbedding
from app.models.vault import VaultConfig, Conflict
from app.models.agent import AgentSession, AgentMessage
from app.models.memory import (
    MemoryLongTerm, MemoryLongTermHistory,
    MemorySummary, MemoryEpisode, MemoryProcedure,
    ToolsRegistry,
)
from app.models.event import Event, TaskIdempotency, AccountDeletionLog

__all__ = [
    "Base",
    # user & RBAC
    "User", "OAuthAccount", "Role", "Permission", "UserRole", "RolePermission",
    # LLM keys
    "UserLLMKey", "AgentLLMAssignment", "UserLLMKeyUsage",
    # interviews
    "Company", "Interview", "InterviewQuestion", "InterviewReview",
    # OKR
    "OKRObjective", "OKRKeyResult", "DailyTask",
    # notes
    "Note", "NoteTag", "NoteLink", "NoteEmbedding",
    # vault
    "VaultConfig", "Conflict",
    # agent
    "AgentSession", "AgentMessage",
    # memory
    "MemoryLongTerm", "MemoryLongTermHistory",
    "MemorySummary", "MemoryEpisode", "MemoryProcedure", "ToolsRegistry",
    # events
    "Event", "TaskIdempotency", "AccountDeletionLog",
]
