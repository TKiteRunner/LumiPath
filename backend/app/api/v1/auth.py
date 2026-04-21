"""API v1 路由：认证相关。"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.schemas.auth import GoogleCallbackRequest, LoginRequest, RefreshRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_async_session)):
    """邮箱 + 密码登录，返回 access + refresh token。"""
    # TODO: call auth_service.login(body.email, body.password, db)
    raise NotImplementedError


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_async_session)):
    """使用 refresh_token 换新的 access_token。"""
    # TODO: call auth_service.refresh(body.refresh_token, db)
    raise NotImplementedError


@router.post("/google")
async def google_oauth(body: GoogleCallbackRequest, db: AsyncSession = Depends(get_async_session)):
    """Google OAuth code exchange。"""
    # TODO: call auth_service.google_login(body.code, db)
    raise NotImplementedError


@router.post("/logout")
async def logout(db: AsyncSession = Depends(get_async_session)):
    """撤销 refresh_token（加入 Redis 黑名单）。"""
    # TODO: call auth_service.logout(refresh_token, db)
    raise NotImplementedError
