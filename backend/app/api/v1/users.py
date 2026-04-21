"""API v1 路由：用户 + LLM Key 管理。"""
import uuid

from fastapi import APIRouter, Depends
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
    # TODO: user_service.update(current_user.id, body, db)
    raise NotImplementedError


# ── LLM Key CRUD ─────────────────────────────────────────────────────────────
@router.get("/me/llm-keys", response_model=list[LLMKeyRead])
async def list_llm_keys(current_user: CurrentUser, db: AsyncSession = Depends(get_async_session)):
    # TODO: llm_key_service.list(current_user.id, db)
    raise NotImplementedError


@router.post("/me/llm-keys", response_model=LLMKeyRead, status_code=201)
async def create_llm_key(
    body: LLMKeyCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
    _: None = require_permission("llm_key:manage"),
):
    # TODO: llm_key_service.create(current_user.id, body, db)
    raise NotImplementedError


@router.delete("/me/llm-keys/{key_id}", status_code=204)
async def delete_llm_key(
    key_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
):
    # TODO: llm_key_service.delete(key_id, current_user.id, db)
    raise NotImplementedError


# ── Agent API Key 指派 ────────────────────────────────────────────────────────
@router.get("/me/agent-assignments", response_model=list[AgentAssignmentRead])
async def list_agent_assignments(current_user: CurrentUser, db: AsyncSession = Depends(get_async_session)):
    # TODO
    raise NotImplementedError


@router.put("/me/agent-assignments", response_model=AgentAssignmentRead)
async def upsert_agent_assignment(
    body: AgentAssignmentCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_async_session),
):
    # TODO
    raise NotImplementedError
