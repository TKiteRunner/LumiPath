"""
JWT 签发 / 验证 + bcrypt 密码哈希
"""
from datetime import datetime, timedelta, timezone
from typing import Any
import uuid

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# ── bcrypt ────────────────────────────────────────────────────────────────────
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────
def _create_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    payload = data.copy()
    now = datetime.now(tz=timezone.utc)
    payload.update({
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
    })
    return jwt.encode(payload, settings.app_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str, roles: list[str] | None = None) -> str:
    return _create_token(
        data={"sub": user_id, "type": "access", "roles": roles or []},
        expires_delta=timedelta(minutes=settings.jwt_access_expire_minutes),
    )


def create_refresh_token(user_id: str) -> tuple[str, str]:
    """返回 (refresh_token, jti)，jti 用于存入 Redis 黑名单。"""
    jti = str(uuid.uuid4())
    token = _create_token(
        data={"sub": user_id, "type": "refresh", "jti": jti},
        expires_delta=timedelta(days=settings.jwt_refresh_expire_days),
    )
    return token, jti


def decode_token(token: str) -> dict[str, Any]:
    """解码 JWT，失败抛 JWTError。"""
    return jwt.decode(token, settings.app_secret_key, algorithms=[settings.jwt_algorithm])
