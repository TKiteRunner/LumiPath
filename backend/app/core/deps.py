"""
FastAPI Dependencies: 当前用户提取 + 权限校验
"""
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token, is_token_blacklisted
from app.db.session import get_async_session
from app.models.user import Permission, Role, RolePermission, User, UserRole


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_async_session),
) -> User:
    """
    从 Authorization: Bearer <token> 中提取并验证用户。
    同时检查 jti 是否在 Redis 黑名单中（logout 立即失效）。
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not authorization or not authorization.startswith("Bearer "):
        raise credentials_exc

    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exc
        user_id: str = payload["sub"]
        jti: str | None = payload.get("jti")
    except (JWTError, KeyError):
        raise credentials_exc

    # Redis 黑名单检查（access token 也可能因强制 logout 而失效）
    if jti and await is_token_blacklisted(jti):
        raise credentials_exc

    result = await db.execute(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exc
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_user_permissions(user: User, db: AsyncSession) -> set[str]:
    """拉取用户所有权限 code 集合（走 role → role_permissions 链）。"""
    stmt = (
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id)
    )
    result = await db.execute(stmt)
    return {row[0] for row in result.all()}


def require_permission(permission_code: str):
    """
    用法：
        @router.get("/...", dependencies=[Depends(require_permission("note:write"))])
    """
    async def _check(
        current_user: CurrentUser,
        db: AsyncSession = Depends(get_async_session),
    ) -> None:
        codes = await get_user_permissions(current_user, db)
        if permission_code not in codes and "admin:all" not in codes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission_code}",
            )

    return Depends(_check)
