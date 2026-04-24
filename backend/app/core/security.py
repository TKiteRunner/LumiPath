"""
JWT 签发 / 验证 + bcrypt 密码哈希 + Redis Token 黑名单
"""
from datetime import datetime, timedelta, timezone
from typing import Any
import uuid

import bcrypt as _bcrypt
from jose import JWTError, jwt

from app.config import settings

# ── bcrypt (direct, passlib-free for bcrypt 4.x+ compatibility) ──────────────

def hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


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
    """返回 (refresh_token, jti)，jti 用于存入 Redis 白名单 / 黑名单。"""
    jti = str(uuid.uuid4())
    token = _create_token(
        data={"sub": user_id, "type": "refresh", "jti": jti},
        expires_delta=timedelta(days=settings.jwt_refresh_expire_days),
    )
    return token, jti


def decode_token(token: str) -> dict[str, Any]:
    """解码 JWT，失败抛 JWTError。"""
    return jwt.decode(token, settings.app_secret_key, algorithms=[settings.jwt_algorithm])


# ── Redis Token 黑名单 ────────────────────────────────────────────────────────
# 黑名单 key 格式：bl:jti:{jti}
# 白名单 key 格式：refresh:{jti}  （value = user_id，用于双重验证）

_BL_PREFIX = "bl:jti:"
_RT_PREFIX = "refresh:"


async def store_refresh_token(jti: str, user_id: str, ttl_seconds: int) -> None:
    """登录 / 注册时将合法 refresh token jti 写入 Redis 白名单。"""
    from app.db.redis import get_redis, jitter_ttl
    redis = get_redis()
    await redis.setex(f"{_RT_PREFIX}{jti}", jitter_ttl(ttl_seconds), user_id)


async def blacklist_refresh_token(jti: str, ttl_seconds: int) -> None:
    """logout / token 轮换时将旧 jti 加入黑名单。"""
    from app.db.redis import get_redis, jitter_ttl
    redis = get_redis()
    # 写入黑名单
    await redis.setex(f"{_BL_PREFIX}{jti}", jitter_ttl(ttl_seconds), "1")
    # 同时删除白名单记录
    await redis.delete(f"{_RT_PREFIX}{jti}")


async def is_token_blacklisted(jti: str) -> bool:
    """检查 jti 是否在黑名单中（True = 已失效）。"""
    from app.db.redis import get_redis
    redis = get_redis()
    return bool(await redis.exists(f"{_BL_PREFIX}{jti}"))


async def is_refresh_token_valid(jti: str) -> bool:
    """检查 refresh token jti 是否在白名单中（True = 合法）。"""
    from app.db.redis import get_redis
    redis = get_redis()
    return bool(await redis.exists(f"{_RT_PREFIX}{jti}"))
