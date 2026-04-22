"""
Redis 连接池 + 工具函数。
- jitter_ttl: TTL 随机抖动，防雪崩
- bloom_add / bloom_check: 布隆过滤器，防穿透（依赖 redis-stack / RedisBloom）
- get_redis: 返回绑定到连接池的 Redis 客户端
"""
from __future__ import annotations

import json
import random
from typing import Any

from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool

from app.config import settings

_pool: ConnectionPool | None = None

# ── 生命周期 ──────────────────────────────────────────────────────────────────

async def init_redis_pool() -> None:
    global _pool
    kwargs: dict[str, Any] = {
        "max_connections": 20,
        "decode_responses": True,
        "socket_timeout": 5,
        "socket_connect_timeout": 3,
    }
    if settings.redis_password:
        kwargs["password"] = settings.redis_password
    _pool = ConnectionPool.from_url(settings.redis_url, **kwargs)


async def close_redis_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


def get_redis() -> Redis:
    if _pool is None:
        raise RuntimeError("Redis pool not initialized — call init_redis_pool() in lifespan")
    return Redis(connection_pool=_pool)


# ── TTL 工具 ──────────────────────────────────────────────────────────────────

def jitter_ttl(base_seconds: int, pct: float = 0.1) -> int:
    """在 base_seconds ± pct% 范围内随机抖动，防止大量 key 同时过期造成雪崩。"""
    delta = max(1, int(base_seconds * pct))
    return base_seconds + random.randint(-delta, delta)


# ── 分布式锁（防击穿）────────────────────────────────────────────────────────

class RedisLock:
    """
    简单分布式锁：SET NX EX。
    用法：async with RedisLock(redis, "lock:note:xxx", ttl=10): ...
    """

    def __init__(self, redis: Redis, key: str, ttl: int = 30) -> None:
        self._redis = redis
        self._key = key
        self._ttl = ttl
        self._acquired = False

    async def __aenter__(self) -> "RedisLock":
        self._acquired = await self._redis.set(self._key, "1", nx=True, ex=self._ttl)
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._acquired:
            await self._redis.delete(self._key)

    @property
    def acquired(self) -> bool:
        return bool(self._acquired)


# ── 布隆过滤器（防穿透）──────────────────────────────────────────────────────

_BLOOM_KEY = "lumipath:bloom:notes"
_BLOOM_CAPACITY = 1_000_000
_BLOOM_ERROR_RATE = 0.01


async def bloom_init(redis: Redis) -> None:
    """首次启动时创建布隆过滤器（幂等）。降级：若 RedisBloom 不可用则跳过。"""
    try:
        await redis.execute_command(
            "BF.RESERVE", _BLOOM_KEY, _BLOOM_ERROR_RATE, _BLOOM_CAPACITY, "NONSCALING"
        )
    except Exception:
        # BF.RESERVE 在 key 已存在时会报错，忽略；RedisBloom 缺失时也忽略
        pass


async def bloom_add(redis: Redis, value: str) -> None:
    try:
        await redis.execute_command("BF.ADD", _BLOOM_KEY, value)
    except Exception:
        pass


async def bloom_check(redis: Redis, value: str) -> bool:
    """返回 True 表示"可能存在"，False 表示"一定不存在"。"""
    try:
        return bool(await redis.execute_command("BF.EXISTS", _BLOOM_KEY, value))
    except Exception:
        return True  # RedisBloom 不可用时保守返回 True，降级为正常查询


# ── 空值缓存（防穿透降级方案）────────────────────────────────────────────────

_NULL_VALUE = "__null__"
_NULL_TTL = 60  # 短 TTL 避免脏数据长期存在


async def cache_get(redis: Redis, key: str) -> tuple[bool, Any]:
    """
    返回 (hit, value)。
    hit=True + value=None 表示命中空值缓存（对象在 DB 中不存在）。
    hit=False 表示缓存未命中。
    """
    raw = await redis.get(key)
    if raw is None:
        return False, None
    if raw == _NULL_VALUE:
        return True, None
    return True, json.loads(raw)


async def cache_set(redis: Redis, key: str, value: Any | None, ttl: int = 300) -> None:
    if value is None:
        await redis.setex(key, _NULL_TTL, _NULL_VALUE)
    else:
        await redis.setex(key, jitter_ttl(ttl), json.dumps(value, ensure_ascii=False, default=str))
