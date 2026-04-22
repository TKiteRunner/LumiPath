"""
Short-term Memory — Redis HSET / HGET / EXPIRE。
key 命名空间: short:{user_id}
每个 field 的 value 是 JSON 序列化的字符串。
"""
from __future__ import annotations

import json
import structlog
from typing import Any

from app.agents.memory.base import BaseMemory
from app.db.redis import get_redis, jitter_ttl

logger = structlog.get_logger(__name__)

_NS = "short"
_DEFAULT_TTL = 3600  # 1 小时


class ShortTermMemory(BaseMemory):

    def _hkey(self) -> str:
        return f"{_NS}:{self.user_id}"

    async def read(self, key: str, **kwargs) -> Any:
        """
        key 为空时 HGETALL 返回完整 dict；
        key 非空时 HGET 返回单个字段值。
        """
        redis = get_redis()
        hkey = self._hkey()
        try:
            if not key:
                raw: dict[str, str] = await redis.hgetall(hkey)
                return {k: _loads(v) for k, v in raw.items()} if raw else {}
            raw_val = await redis.hget(hkey, key)
            return _loads(raw_val) if raw_val is not None else None
        except Exception as exc:
            logger.warning("ShortTermMemory.read failed", user_id=self.user_id, key=key, error=str(exc))
            return None

    async def write(self, data: dict, ttl: int = _DEFAULT_TTL, **kwargs) -> None:
        """
        将 data dict 的每个 key 写入 Redis Hash，并刷新整体 Hash 的 TTL。
        使用 pipeline 保证原子性。
        """
        if not data:
            return
        redis = get_redis()
        hkey = self._hkey()
        try:
            pipe = redis.pipeline()
            for k, v in data.items():
                pipe.hset(hkey, k, json.dumps(v, ensure_ascii=False, default=str))
            pipe.expire(hkey, jitter_ttl(ttl))
            await pipe.execute()
            logger.debug("ShortTermMemory.write", user_id=self.user_id, fields=list(data.keys()))
        except Exception as exc:
            logger.warning("ShortTermMemory.write failed", user_id=self.user_id, error=str(exc))

    async def search(self, query: str, top_k: int = 5, **kwargs) -> list[dict]:
        # Redis Hash 不支持全文检索；返回全量快照供上层筛选
        snap = await self.read("")
        if not isinstance(snap, dict):
            return []
        return [{"key": k, "value": v} for k, v in snap.items()][:top_k]

    async def delete(self, key: str) -> None:
        redis = get_redis()
        await redis.hdel(self._hkey(), key)

    async def clear(self) -> None:
        redis = get_redis()
        await redis.delete(self._hkey())


def _loads(raw: str | None) -> Any:
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw
