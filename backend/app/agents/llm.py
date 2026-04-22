"""
LiteLLM 封装：embedding + chat completion。
统一处理 per-user / per-agent API Key 路由和系统兜底 Key。
"""
from __future__ import annotations

import structlog
from typing import Any

import litellm

from app.config import settings

logger = structlog.get_logger(__name__)

# 默认向量维度（text-embedding-3-small = 1536）
DEFAULT_EMBED_MODEL = "text-embedding-3-small"
DEFAULT_EMBED_DIM = 1536


def _configure_fallback_keys() -> None:
    """将系统兜底 API Key 注入 litellm。"""
    if settings.fallback_openai_api_key:
        litellm.openai_key = settings.fallback_openai_api_key
    if settings.fallback_anthropic_api_key:
        litellm.anthropic_key = settings.fallback_anthropic_api_key


_configure_fallback_keys()


async def embed(
    texts: list[str],
    model: str = DEFAULT_EMBED_MODEL,
    api_key: str | None = None,
) -> list[list[float]]:
    """
    批量 embedding。返回与 texts 等长的向量列表。
    api_key 为 None 时使用系统兜底 Key。
    """
    if not texts:
        return []
    kwargs: dict[str, Any] = {"model": model, "input": texts}
    if api_key:
        kwargs["api_key"] = api_key
    try:
        resp = await litellm.aembedding(**kwargs)
        return [item["embedding"] for item in resp.data]
    except Exception as exc:
        logger.error("embedding failed", model=model, error=str(exc))
        raise


async def embed_one(
    text: str,
    model: str = DEFAULT_EMBED_MODEL,
    api_key: str | None = None,
) -> list[float]:
    vectors = await embed([text], model=model, api_key=api_key)
    return vectors[0]


async def chat(
    messages: list[dict[str, str]],
    model: str = "gpt-4o-mini",
    api_key: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    **kwargs: Any,
) -> str:
    """
    单轮 / 多轮对话，返回 assistant 文本。
    """
    call_kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        **kwargs,
    }
    if api_key:
        call_kwargs["api_key"] = api_key
    try:
        resp = await litellm.acompletion(**call_kwargs)
        return resp.choices[0].message.content or ""
    except Exception as exc:
        logger.error("chat completion failed", model=model, error=str(exc))
        raise


def vec_to_pg(vector: list[float]) -> str:
    """将 Python float list 转为 pgvector 接受的字符串格式 '[1.0,2.0,...]'。"""
    return "[" + ",".join(str(v) for v in vector) + "]"
