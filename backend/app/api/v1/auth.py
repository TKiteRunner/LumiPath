"""API v1 路由：认证相关。"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.schemas.auth import GoogleCallbackRequest, LoginRequest, RefreshRequest, TokenResponse
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(LoginRequest):
    display_name: str


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_async_session)):
    """邮箱 + 密码注册新账号，返回 access + refresh token。"""
    return await auth_service.register(body.email, body.password, body.display_name, db)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_async_session)):
    """邮箱 + 密码登录，返回 access + refresh token。"""
    return await auth_service.login(body.email, body.password, db)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_async_session)):
    """使用 refresh_token 换新的 access_token。"""
    return await auth_service.refresh(body.refresh_token, db)


@router.post("/google/callback", response_model=TokenResponse)
@router.post("/google")
async def google_oauth(body: GoogleCallbackRequest, db: AsyncSession = Depends(get_async_session)):
    """Google OAuth code exchange。"""
    return await auth_service.google_login(body.code, db)


@router.post("/logout")
async def logout(body: RefreshRequest):
    """撤销 refresh_token（加入 Redis 黑名单）。"""
    await auth_service.logout(body.refresh_token)
    return {"detail": "logged out"}
