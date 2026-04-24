"""
Memory Agent — 多层记忆检索 + 记忆固化
retriever → planner → executor → reflector → memory_writer
"""
from __future__ import annotations

import json
import structlog
from langchain_core.messages import AIMessage
from langgraph.types import Command

from app.agents.state import AgentState
from app.agents.memory.manager import MemoryManager

logger = structlog.get_logger(__name__)

_SYSTEM_PROMPT = "你是记忆检索助手（Memory Assistant），专门帮助用户从历史记录中召回相关信息并进行总结归纳。请用中文回复。"


async def _retriever(state: AgentState) -> tuple[str, dict]:
    query = state["messages"][-1].content if state["messages"] else ""
    mgr = MemoryManager(state["user_id"])
    retrieved = await mgr.retrieve_context(query)
    return query, retrieved


async def _synthesize(query: str, retrieved: dict, user_id: str) -> str:
    """用 LLM 把各层记忆融合成自然语言回复。"""
    fused = retrieved.get("fused_context", {})
    long_term = retrieved.get("long_term") or {}

    context_parts = []
    if long_term:
        context_parts.append(f"长期记忆（能力画像）：{json.dumps(long_term, ensure_ascii=False)[:400]}")
    if fused.get("summaries"):
        context_parts.append(f"摘要记忆：{str(fused['summaries'])[:400]}")
    if fused.get("episodes"):
        context_parts.append(f"情景记忆：{str(fused['episodes'])[:400]}")
    if fused.get("semantics"):
        context_parts.append(f"语义图谱：{str(fused['semantics'])[:400]}")

    if not context_parts:
        return "目前尚未积累足够的记忆数据，随着您使用系统的时间增长，我能提供更丰富的个性化回忆。"

    from app.agents.utils.llm_client import get_llm_config, get_system_prompt
    cfg = await get_llm_config(user_id, "memory")
    if not cfg:
        return "（请配置 LLM API Key 以获取 AI 综合分析）\n\n已检索到的记忆：\n" + "\n".join(context_parts)

    system_prompt = await get_system_prompt(user_id, "memory")
    try:
        import litellm
        context_str = "\n".join(context_parts)
        resp = await litellm.acompletion(
            **cfg.litellm_kwargs(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"用户问题：{query}\n\n从记忆系统检索到以下信息：\n{context_str}\n\n请综合这些信息给用户一个有帮助的回答。"},
            ],
            max_tokens=800,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        logger.warning("memory synthesize failed", error=str(exc))
        return "已从记忆系统召回以下信息：\n" + "\n".join(context_parts)


async def memory_agent(state: AgentState) -> Command[str]:
    """记忆检索专家 — retriever→synthesize→memory_writer。"""
    try:
        query, retrieved = await _retriever(state)
        final_response = await _synthesize(query, retrieved, state["user_id"])

        # 将本次检索记录到程序记忆
        mgr = MemoryManager(state["user_id"])
        await mgr.procedural.write({
            "agent": "memory_agent",
            "query": query[:200],
            "response_summary": final_response[:200],
        })
    except Exception as exc:
        logger.error("memory_agent pipeline error", error=str(exc))
        final_response = f"抱歉，记忆检索时出现错误：{exc}"

    return Command(
        goto="supervisor",
        update={"messages": [AIMessage(content=final_response)], "current_agent": None},
    )
