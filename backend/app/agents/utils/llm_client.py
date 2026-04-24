"""
LLM config resolver for agents.

Priority: agent-specific override > user default > env fallback
"""
from __future__ import annotations

from dataclasses import dataclass

import structlog
from sqlalchemy.future import select

logger = structlog.get_logger(__name__)

# Provider → (litellm model string, api_base or None)
_PROVIDER_DEFAULTS: dict[str, tuple[str, str | None]] = {
    "anthropic": ("anthropic/claude-haiku-4-5-20251001", None),
    "openai":    ("openai/gpt-4o-mini",                  None),
    "deepseek":  ("openai/deepseek-chat",                "https://api.deepseek.com/v1"),
    "qwen":      ("openai/qwen-plus",                    "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    "gemini":    ("gemini/gemini-1.5-flash",             None),
    "doubao":    ("openai/doubao-pro-32k",               "https://ark.volces.com/api/v3"),
    "kimi":      ("openai/moonshot-v1-8k",               "https://api.moonshot.cn/v1"),
    "minimax":   ("openai/abab6.5s-chat",                "https://api.minimax.chat/v1"),
    "zhipu":     ("openai/glm-4-flash",                  "https://open.bigmodel.cn/api/paas/v4/"),
}


@dataclass
class LLMConfig:
    model: str
    api_key: str
    api_base: str | None = None

    def litellm_kwargs(self) -> dict:
        kwargs: dict = {"model": self.model, "api_key": self.api_key}
        if self.api_base:
            kwargs["api_base"] = self.api_base
        return kwargs


def _env_fallback(agent_name: str | None = None) -> LLMConfig | None:
    """Read from environment fallback keys. SiliconFlow takes priority when configured."""
    from app.config import settings

    # SiliconFlow — per-agent model routing
    if settings.siliconflow_api_key:
        _agent_model_map: dict[str | None, str] = {
            "interview": settings.llm_ia,
            "okr":       settings.llm_oa,
            "memory":    settings.llm_ma,
            "notes":     settings.llm_oa,
        }
        model = _agent_model_map.get(agent_name) or settings.llm_supervisor
        return LLMConfig(
            model=model,
            api_key=settings.siliconflow_api_key,
            api_base=settings.siliconflow_api_base,
        )

    if settings.fallback_anthropic_api_key:
        return LLMConfig(model="anthropic/claude-haiku-4-5-20251001", api_key=settings.fallback_anthropic_api_key)
    if settings.fallback_openai_api_key:
        return LLMConfig(model="openai/gpt-4o-mini", api_key=settings.fallback_openai_api_key)
    if settings.fallback_deepseek_api_key:
        return LLMConfig(model="openai/deepseek-chat", api_key=settings.fallback_deepseek_api_key, api_base="https://api.deepseek.com/v1")
    if settings.fallback_qwen_api_key:
        return LLMConfig(model="openai/qwen-plus", api_key=settings.fallback_qwen_api_key, api_base="https://dashscope.aliyuncs.com/compatible-mode/v1")
    if settings.fallback_gemini_api_key:
        return LLMConfig(model="gemini/gemini-1.5-flash", api_key=settings.fallback_gemini_api_key)
    if settings.fallback_doubao_api_key:
        return LLMConfig(model="openai/doubao-pro-32k", api_key=settings.fallback_doubao_api_key, api_base="https://ark.volces.com/api/v3")
    if settings.fallback_kimi_api_key:
        return LLMConfig(model="openai/moonshot-v1-8k", api_key=settings.fallback_kimi_api_key, api_base="https://api.moonshot.cn/v1")
    if settings.fallback_minimax_api_key:
        return LLMConfig(model="openai/abab6.5s-chat", api_key=settings.fallback_minimax_api_key, api_base="https://api.minimax.chat/v1")
    if settings.fallback_zhipu_api_key:
        return LLMConfig(model="openai/glm-4-flash", api_key=settings.fallback_zhipu_api_key, api_base="https://open.bigmodel.cn/api/paas/v4/")
    return None


def _load_skill_default(filename: str) -> str:
    import pathlib
    path = pathlib.Path(__file__).parent.parent / "skills" / filename
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


_DEFAULT_SYSTEM_PROMPTS: dict[str, str] = {
    "interview": _load_skill_default("interview-agent.md"),
    "notes":     _load_skill_default("notes-agent.md"),
    "okr":       _load_skill_default("okr-agent.md"),
    "memory":    _load_skill_default("memory-agent.md"),
}


async def get_system_prompt(user_id: str, agent_name: str) -> str:
    """返回用户自定义的系统提示词，未配置时返回默认值。"""
    try:
        from app.db.engine import AsyncSessionLocal
        from app.models.user import User

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

        if user and user.preferences:
            custom = user.preferences.get("agent_skills", {}).get(agent_name, "")
            if custom:
                return custom
    except Exception as exc:
        logger.warning("get_system_prompt db lookup failed", error=str(exc))

    return _DEFAULT_SYSTEM_PROMPTS.get(agent_name, "你是一个有帮助的 AI 助手，请用中文回复。")


async def get_llm_config(user_id: str, agent_name: str | None = None) -> LLMConfig | None:
    """
    Resolve LLM config for a user+agent pair.
    Returns None if no key is configured anywhere.
    """
    try:
        from app.db.engine import AsyncSessionLocal
        from app.models.user import User

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

        if user and user.preferences:
            llm_settings = user.preferences.get("llm_settings", {})

            # Check agent-specific override first
            if agent_name:
                assignment = llm_settings.get("agent_assignments", {}).get(agent_name, {})
                provider = assignment.get("provider", "")
                api_key = assignment.get("api_key", "")
                if provider and api_key:
                    model, api_base = _PROVIDER_DEFAULTS.get(provider, (_PROVIDER_DEFAULTS["openai"][0], None))
                    return LLMConfig(model=model, api_key=api_key, api_base=api_base)

            # Fall back to user default
            provider = llm_settings.get("default_provider", "")
            api_key = llm_settings.get("default_api_key", "")
            if provider and api_key:
                model, api_base = _PROVIDER_DEFAULTS.get(provider, (_PROVIDER_DEFAULTS["openai"][0], None))
                return LLMConfig(model=model, api_key=api_key, api_base=api_base)

    except Exception as exc:
        logger.warning("get_llm_config db lookup failed", error=str(exc))

    return _env_fallback(agent_name)
