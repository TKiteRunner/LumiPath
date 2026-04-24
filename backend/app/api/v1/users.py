"""API v1 路由：用户 + LLM Key 管理。"""
import uuid
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_permission
from app.db.session import get_async_session
from app.schemas.user import AgentAssignmentCreate, AgentAssignmentRead, LLMKeyCreate, LLMKeyRead, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def get_me(current_user: CurrentUser):
    """获取当前用户信息。"""
    return current_user


@router.patch("/me", response_model=UserRead)
async def update_me(body: UserUpdate, current_user: CurrentUser, db: AsyncSession = Depends(get_async_session)):
    """更新用户基本信息。"""
    data = body.model_dump(exclude_none=True)
    for k, v in data.items():
        setattr(current_user, k, v)
    await db.commit()
    await db.refresh(current_user)
    return current_user


# ── LLM Settings (simplified, stored in user.preferences) ────────────────────

class LLMSettingsResponse(BaseModel):
    default_provider: str = "anthropic"
    default_api_key: str = ""
    agent_assignments: dict[str, dict[str, str]] = {}


@router.get("/me/settings/llm", response_model=LLMSettingsResponse)
async def get_llm_settings(current_user: CurrentUser):
    """获取 LLM 设置（存储于 user.preferences）。"""
    llm = current_user.preferences.get("llm_settings", {})
    return LLMSettingsResponse(
        default_provider=llm.get("default_provider", "anthropic"),
        default_api_key=llm.get("default_api_key", ""),
        agent_assignments=llm.get("agent_assignments", {}),
    )


@router.patch("/me/settings/llm", response_model=LLMSettingsResponse)
async def update_llm_settings(
    body: LLMSettingsResponse,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
):
    """保存 LLM 设置（存储于 user.preferences）。"""
    prefs = dict(current_user.preferences or {})
    prefs["llm_settings"] = body.model_dump()
    current_user.preferences = prefs
    await db.commit()
    return body


# ── Agent Skills (system prompts) ────────────────────────────────────────────

def _load_skill(filename: str) -> str:
    """Load default skill content from the bundled markdown files."""
    import pathlib
    path = pathlib.Path(__file__).parent.parent.parent / "agents" / "skills" / filename
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


DEFAULT_AGENT_SKILLS: dict[str, str] = {
    "interview": _load_skill("interview-agent.md"),
    "notes":     _load_skill("notes-agent.md"),
    "okr":       _load_skill("okr-agent.md"),
    "memory":    _load_skill("memory-agent.md"),
}


class AgentSkillsResponse(BaseModel):
    skills: dict[str, str] = {}


@router.get("/me/settings/skills", response_model=AgentSkillsResponse)
async def get_agent_skills(current_user: CurrentUser):
    """获取用户自定义的 Agent 系统提示词，未自定义的返回默认值。"""
    saved = (current_user.preferences or {}).get("agent_skills", {})
    merged = {k: saved.get(k, v) for k, v in DEFAULT_AGENT_SKILLS.items()}
    return AgentSkillsResponse(skills=merged)


@router.patch("/me/settings/skills", response_model=AgentSkillsResponse)
async def update_agent_skills(
    body: AgentSkillsResponse,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
):
    """保存用户自定义的 Agent 系统提示词。"""
    prefs = dict(current_user.preferences or {})
    prefs["agent_skills"] = body.skills
    current_user.preferences = prefs
    await db.commit()
    return body


# ── LLM Key CRUD ─────────────────────────────────────────────────────────────
@router.get("/me/llm-keys", response_model=list[LLMKeyRead])
async def list_llm_keys(current_user: CurrentUser, db: AsyncSession = Depends(get_async_session)):
    raise NotImplementedError


@router.post("/me/llm-keys", response_model=LLMKeyRead, status_code=201)
async def create_llm_key(
    body: LLMKeyCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
    _: None = require_permission("llm_key:manage"),
):
    raise NotImplementedError


@router.delete("/me/llm-keys/{key_id}", status_code=204)
async def delete_llm_key(
    key_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
):
    raise NotImplementedError


# ── Agent API Key 指派 ────────────────────────────────────────────────────────
@router.get("/me/agent-assignments", response_model=list[AgentAssignmentRead])
async def list_agent_assignments(current_user: CurrentUser, db: AsyncSession = Depends(get_async_session)):
    raise NotImplementedError


@router.put("/me/agent-assignments", response_model=AgentAssignmentRead)
async def upsert_agent_assignment(
    body: AgentAssignmentCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
):
    raise NotImplementedError
