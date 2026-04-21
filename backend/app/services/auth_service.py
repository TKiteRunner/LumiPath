"""
认证服务骨架：登录 / 注册 / token 刷新 / Google OAuth
Step 3 完善 Redis refresh_token 黑名单写入。
"""
from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.core.exceptions import BadRequestError, UnauthorizedError

logger = structlog.get_logger(__name__)


class AuthService:
    async def login(self, email: str, password: str, db: AsyncSession) -> dict:
        """
        邮箱密码登录。
        返回 {"access_token": ..., "refresh_token": ...}
        """
        from sqlalchemy import select
        from app.models.user import User

        result = await db.execute(
            select(User).where(User.email == email, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()
        if not user or not user.password_hash:
            raise UnauthorizedError("Invalid email or password")
        if not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")

        roles = await self._get_role_names(user.id, db)
        access_token = create_access_token(str(user.id), roles)
        refresh_token, jti = create_refresh_token(str(user.id))

        # TODO Step 3: await redis.setex(f"refresh_token:{jti}", settings.jwt_refresh_expire_days * 86400, str(user.id))
        logger.info("user logged in", user_id=str(user.id))
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    async def register(self, email: str, password: str, display_name: str, db: AsyncSession) -> dict:
        """注册新用户（邮箱 + 密码）。"""
        from sqlalchemy import select
        from app.models.user import User, Role, UserRole
        from datetime import datetime, timezone

        result = await db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise BadRequestError("Email already registered")

        user = User(
            email=email,
            password_hash=hash_password(password),
            display_name=display_name,
        )
        db.add(user)
        await db.flush()

        # 默认赋予 free_user 角色
        free_role = (await db.execute(select(Role).where(Role.name == "free_user"))).scalar_one_or_none()
        if free_role:
            db.add(UserRole(user_id=user.id, role_id=free_role.id, granted_at=datetime.now(timezone.utc)))

        await db.flush()
        roles = ["free_user"]
        access_token = create_access_token(str(user.id), roles)
        refresh_token, _ = create_refresh_token(str(user.id))
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    async def google_login(self, code: str, db: AsyncSession) -> dict:
        """Google OAuth code exchange → upsert user → 颁发 JWT。"""
        # TODO Step 3:
        #   1. httpx 调用 Google token endpoint 换取 id_token
        #   2. 解析 id_token 得到 google_sub / email / name / avatar
        #   3. upsert users + oauth_accounts
        #   4. 颁发 JWT
        raise NotImplementedError("google_login will be implemented in Step 3")

    async def refresh(self, refresh_token_str: str, db: AsyncSession) -> dict:
        """用 refresh_token 换新 access_token。"""
        from app.core.security import decode_token
        from jose import JWTError
        from sqlalchemy import select
        from app.models.user import User

        try:
            payload = decode_token(refresh_token_str)
            if payload.get("type") != "refresh":
                raise UnauthorizedError("Invalid token type")
            # TODO Step 3: check jti not in Redis blacklist
            user_id = payload["sub"]
        except (JWTError, KeyError):
            raise UnauthorizedError("Invalid refresh token")

        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user:
            raise UnauthorizedError("User not found")

        roles = await self._get_role_names(user.id, db)
        new_access = create_access_token(str(user.id), roles)
        new_refresh, new_jti = create_refresh_token(str(user.id))
        # TODO Step 3: 旧 jti 加入黑名单，新 jti 写入 Redis
        return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}

    async def logout(self, refresh_token_str: str) -> None:
        """将 refresh_token jti 加入 Redis 黑名单（stub）。"""
        # TODO Step 3: decode → get jti → redis.delete(f"refresh_token:{jti}")
        logger.info("logout (stub): refresh_token blacklist not yet implemented")

    # ── helpers ──────────────────────────────────────────────────────────────
    @staticmethod
    async def _get_role_names(user_id, db: AsyncSession) -> list[str]:
        from sqlalchemy import select
        from app.models.user import Role, UserRole
        result = await db.execute(
            select(Role.name).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user_id)
        )
        return [row[0] for row in result.all()]


auth_service = AuthService()
