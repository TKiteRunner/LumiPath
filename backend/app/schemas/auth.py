"""Pydantic v2 schemas for auth."""
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleCallbackRequest(BaseModel):
    code: str
    redirect_uri: str | None = None


class UserInToken(BaseModel):
    id: str
    email: str
    display_name: str
    avatar_url: str | None = None
    roles: list[str]


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserInToken


class RefreshRequest(BaseModel):
    refresh_token: str
