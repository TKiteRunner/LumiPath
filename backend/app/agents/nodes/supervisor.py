"""
Supervisor Agent 节点：意图分类 + 路由。
使用 LiteLLM 做 zero-shot 分类，LLM 不可用时降级为关键词匹配。
"""
from __future__ import annotations

import structlog
from langchain_core.messages import AIMessage
from langgraph.types import Command

from app.agents.state import AgentState

logger = structlog.get_logger(__name__)

_INTENT_SYSTEM_PROMPT = """\
You are a router for LumiPath, a personal career growth AI system.
Classify the user's message into exactly one label:
- interview : job interviews, technical questions, interview prep, review/feedback
- okr       : OKR goals, key results, progress tracking, daily tasks, quarterly planning
- notes     : daily learning notes, study journal, knowledge base, Obsidian vault
- memory    : recalling past information, knowledge retrieval, history
- general   : greetings, small talk, or anything that doesn't fit above

Reply with ONLY the label (one word, lowercase). No explanation."""

_INTENT_TO_AGENT: dict[str, str] = {
    "interview": "interview_agent",
    "okr": "okr_agent",
    "notes": "notes_agent",
    "memory": "memory_agent",
}

_FALLBACK_KEYWORDS: list[tuple[str, list[str]]] = [
    ("interview", ["面试", "interview", "复盘", "技术题", "笔试", "hr", "offer"]),
    ("okr",       ["okr", "目标", "key result", "kr", "进度", "季度", "打卡"]),
    ("notes",     ["笔记", "note", "日记", "日志", "vault", "obsidian", "学习记录"]),
    ("memory",    ["记忆", "记住", "记录", "历史", "memory", "recall", "回忆"]),
]


def _keyword_fallback(text: str) -> str:
    t = text.lower()
    for intent, keywords in _FALLBACK_KEYWORDS:
        if any(kw in t for kw in keywords):
            return intent
    return "general"


async def _classify_intent(last_msg: str) -> str:
    """LiteLLM 分类，失败时降级关键词。"""
    from app.config import settings
    api_key = settings.fallback_anthropic_api_key or settings.fallback_openai_api_key
    if not api_key:
        return _keyword_fallback(last_msg)

    try:
        import litellm
        model = (
            "anthropic/claude-haiku-4-5-20251001"
            if settings.fallback_anthropic_api_key
            else "openai/gpt-4o-mini"
        )
        resp = await litellm.acompletion(
            model=model,
            messages=[
                {"role": "system", "content": _INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": last_msg[:2000]},
            ],
            max_tokens=10,
            temperature=0.0,
        )
        label = resp.choices[0].message.content.strip().lower()
        return label if label in {*_INTENT_TO_AGENT, "general"} else _keyword_fallback(last_msg)
    except Exception as exc:
        logger.warning("supervisor LLM routing failed, using keyword fallback", error=str(exc))
        return _keyword_fallback(last_msg)


async def supervisor_agent(state: AgentState) -> Command[str]:
    """
    意图分类 → 路由到对应 Specialized Agent 或 END。
    """
    last_msg = state["messages"][-1].content if state["messages"] else ""
    intent = await _classify_intent(last_msg)
    target = _INTENT_TO_AGENT.get(intent)

    logger.info("supervisor routing", intent=intent, target=target or "__end__", user_id=state.get("user_id"))

    if target is None:
        return Command(
            goto="__end__",
            update={
                "messages": [
                    AIMessage(content="您好！我可以帮您处理面试复盘、OKR规划、学习笔记等问题，请告诉我您需要什么？")
                ]
            },
        )
    return Command(goto=target, update={"next_agent": target, "current_agent": target})
