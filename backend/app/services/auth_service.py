"""
认证服务：登录 / 注册 / token 刷新 / Google OAuth
"""
from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import BadRequestError, UnauthorizedError
from app.core.security import (
    blacklist_refresh_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    is_refresh_token_valid,
    store_refresh_token,
    verify_password,
)

logger = structlog.get_logger(__name__)

_REFRESH_TTL = settings.jwt_refresh_expire_days * 86400


class AuthService:

    # ── 邮箱密码登录 ──────────────────────────────────────────────────────────

    async def login(self, email: str, password: str, db: AsyncSession) -> dict:
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
        await store_refresh_token(jti, str(user.id), _REFRESH_TTL)

        logger.info("user logged in", user_id=str(user.id))
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    # ── 注册 ──────────────────────────────────────────────────────────────────

    async def register(self, email: str, password: str, display_name: str, db: AsyncSession) -> dict:
        from datetime import datetime, timezone
        from sqlalchemy import select
        from app.models.user import User, Role, UserRole

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

        free_role = (await db.execute(select(Role).where(Role.name == "free_user"))).scalar_one_or_none()
        if free_role:
            db.add(UserRole(user_id=user.id, role_id=free_role.id, granted_at=datetime.now(timezone.utc)))

        await db.commit()
        await db.refresh(user)

        roles = ["free_user"]
        access_token = create_access_token(str(user.id), roles)
        refresh_token, jti = create_refresh_token(str(user.id))
        await store_refresh_token(jti, str(user.id), _REFRESH_TTL)

        logger.info("user registered", user_id=str(user.id))
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    # ── Google OAuth ──────────────────────────────────────────────────────────

    async def google_login(self, code: str, db: AsyncSession) -> dict:
        """Google OAuth Authorization Code Flow → 颁发 JWT。"""
        import httpx

        async with httpx.AsyncClient(timeout=10) as client:
            # 1. code → token
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": settings.google_redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            if token_resp.status_code != 200:
                raise UnauthorizedError("Google OAuth token exchange failed")
            token_data = token_resp.json()

            # 2. token → userinfo
            userinfo_resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {token_data['access_token']}"},
            )
            if userinfo_resp.status_code != 200:
                raise UnauthorizedError("Failed to fetch Google userinfo")
            userinfo = userinfo_resp.json()

        # 3. upsert User + OAuthAccount
        user = await self._upsert_oauth_user(
            google_sub=userinfo["id"],
            email=userinfo.get("email", ""),
            display_name=userinfo.get("name", ""),
            avatar_url=userinfo.get("picture"),
            db=db,
        )

        # 4. 颁发 JWT
        roles = await self._get_role_names(user.id, db)
        access_token = create_access_token(str(user.id), roles)
        refresh_token, jti = create_refresh_token(str(user.id))
        await store_refresh_token(jti, str(user.id), _REFRESH_TTL)

        logger.info("google oauth login", user_id=str(user.id), email=user.email)
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    # ── Token 刷新 ────────────────────────────────────────────────────────────

    async def refresh(self, refresh_token_str: str, db: AsyncSession) -> dict:
        from jose import JWTError
        from sqlalchemy import select
        from app.models.user import User

        try:
            payload = decode_token(refresh_token_str)
            if payload.get("type") != "refresh":
                raise UnauthorizedError("Invalid token type")
            user_id: str = payload["sub"]
            old_jti: str = payload["jti"]
        except (JWTError, KeyError):
            raise UnauthorizedError("Invalid refresh token")

        # 白名单校验：必须是我们签发的 jti
        if not await is_refresh_token_valid(old_jti):
            raise UnauthorizedError("Refresh token revoked or expired")

        user = (await db.execute(select(User).where(User.id == user_id, User.deleted_at.is_(None)))).scalar_one_or_none()
        if not user:
            raise UnauthorizedError("User not found")

        # 旧 jti 加入黑名单，颁发新 token
        await blacklist_refresh_token(old_jti, _REFRESH_TTL)

        roles = await self._get_role_names(user.id, db)
        new_access = create_access_token(str(user.id), roles)
        new_refresh, new_jti = create_refresh_token(str(user.id))
        await store_refresh_token(new_jti, str(user.id), _REFRESH_TTL)

        logger.info("token refreshed", user_id=str(user.id))
        return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}

    # ── Logout ────────────────────────────────────────────────────────────────

    async def logout(self, refresh_token_str: str) -> None:
        """将 refresh token jti 加入黑名单，立即失效。"""
        from jose import JWTError
        try:
            payload = decode_token(refresh_token_str)
            jti: str = payload.get("jti", "")
            if jti:
                await blacklist_refresh_token(jti, _REFRESH_TTL)
                logger.info("user logged out", jti=jti)
        except JWTError:
            # token 已过期或格式错误，无需处理
            pass

    # ── helpers ──────────────────────────────────────────────────────────────

    async def _upsert_oauth_user(
        self,
        google_sub: str,
        email: str,
        display_name: str,
        avatar_url: str | None,
        db: AsyncSession,
    ):
        from datetime import datetime, timezone
        from sqlalchemy import select
        from app.models.user import User, Role, UserRole, OAuthAccount

        # 先按 google_sub 找 OAuthAccount
        oauth_row = (
            await db.execute(
                select(OAuthAccount).where(
                    OAuthAccount.provider == "google",
                    OAuthAccount.provider_user_id == google_sub,
                )
            )
        ).scalar_one_or_none()

        if oauth_row:
            user = (await db.execute(select(User).where(User.id == oauth_row.user_id))).scalar_one()
        else:
            # 按 email 找已有用户（邮箱密码注册过）
            user = (
                await db.execute(select(User).where(User.email == email, User.deleted_at.is_(None)))
            ).scalar_one_or_none()

            if not user:
                user = User(
                    email=email,
                    display_name=display_name,
                    avatar_url=avatar_url,
                    password_hash=None,
                )
                db.add(user)
                await db.flush()

                free_role = (await db.execute(select(Role).where(Role.name == "free_user"))).scalar_one_or_none()
                if free_role:
                    db.add(UserRole(user_id=user.id, role_id=free_role.id, granted_at=datetime.now(timezone.utc)))

            # 绑定 OAuthAccount
            db.add(OAuthAccount(
                user_id=user.id,
                provider="google",
                provider_user_id=google_sub,
                email=email,
            ))

        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def _get_role_names(user_id, db: AsyncSession) -> list[str]:
        from sqlalchemy import select
        from app.models.user import Role, UserRole
        result = await db.execute(
            select(Role.name).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user_id)
        )
        return [row[0] for row in result.all()]


auth_service = AuthService()
