"""
OKR Agent — retriever → planner → executor → reflector → memory_writer
"""
from __future__ import annotations

import json
import re
import structlog
from langchain_core.messages import AIMessage
from langgraph.types import Command

from app.agents.state import AgentState
from app.agents.memory.manager import MemoryManager
from app.agents.tools.analyze_okr import AnalyzeOKRTool
from app.agents.tools.suggest_tasks import SuggestTasksTool
from app.agents.tools.generate_report import GenerateReportTool

logger = structlog.get_logger(__name__)

_SYSTEM_PROMPT = "你是 OKR 教练（OKR Coach），帮助用户制定目标、追踪进度、拆解每日任务和生成季度报告。请用中文回复。"

_PLANNER_PROMPT = """\
你是 OKR 教练，需要决定调用哪个工具来回答用户问题。

可用工具：
- analyze_okr     : 分析当前 OKR 目标与 KR 完成度（参数 objective_id?: str）
- suggest_tasks   : 基于 KR 进度建议今日任务（参数 kr_id?: str）
- generate_report : 生成 OKR 季度总结报告（参数 quarter?: str，如 "2026-Q2"）
- none            : 直接回复，不调用工具

用户问题：{query}
已召回上下文（摘要）：{context}

请以 JSON 格式回复，仅包含 JSON，不要有其他文字：
{{"tool": "<tool_name>", "params": {{...}}, "reason": "<一句话说明>"}}
如果选择 none：{{"tool": "none", "response": "<直接回复内容>"}}"""


async def _retriever(state: AgentState) -> tuple[str, dict]:
    query = state["messages"][-1].content if state["messages"] else ""
    mgr = MemoryManager(state["user_id"])
    retrieved = await mgr.retrieve_context(query)
    return query, retrieved


async def _planner(query: str, retrieved: dict, user_id: str) -> dict:
    from app.agents.utils.llm_client import get_llm_config
    cfg = await get_llm_config(user_id, "okr")
    if not cfg:
        return {"tool": "none", "response": "（请先在设置页配置 LLM API Key）"}
    try:
        import litellm
        context_str = str(retrieved.get("fused_context", {}))[:800]
        resp = await litellm.acompletion(
            **cfg.litellm_kwargs(),
            messages=[{"role": "user", "content": _PLANNER_PROMPT.format(query=query, context=context_str)}],
            max_tokens=300,
            temperature=0.1,
        )
        raw = resp.choices[0].message.content.strip()
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception as exc:
        logger.warning("okr planner failed", error=str(exc))
    return {"tool": "none", "response": ""}


async def _executor(plan: dict, user_id: str) -> dict:
    tool_map = {
        "analyze_okr": AnalyzeOKRTool,
        "suggest_tasks": SuggestTasksTool,
        "generate_report": GenerateReportTool,
    }
    tool_name = plan.get("tool", "none")
    if tool_name in tool_map:
        tool = tool_map[tool_name]()
        return await tool.execute(user_id, **plan.get("params", {}))
    return {"direct_response": plan.get("response", "")}


async def _reflector(query: str, tool_result: dict, user_id: str) -> str:
    direct = tool_result.get("direct_response", "")
    if direct:
        return direct
    from app.agents.utils.llm_client import get_llm_config, get_system_prompt
    cfg = await get_llm_config(user_id, "okr")
    if not cfg:
        return f"工具执行结果：{tool_result}"
    system_prompt = await get_system_prompt(user_id, "okr")
    try:
        import litellm
        resp = await litellm.acompletion(
            **cfg.litellm_kwargs(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"用户问题：{query}\n\n工具返回：{json.dumps(tool_result, ensure_ascii=False)}"},
            ],
            max_tokens=800,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        logger.warning("okr reflector failed", error=str(exc))
        return f"处理完成。结果：{tool_result}"


async def _memory_writer(user_id: str, query: str, response: str) -> None:
    mgr = MemoryManager(user_id)
    await mgr.procedural.write({
        "agent": "okr_agent",
        "query": query[:200],
        "response_summary": response[:200],
    })


async def okr_agent(state: AgentState) -> Command[str]:
    """OKR 教练 — retriever→planner→executor→reflector→memory_writer。"""
    try:
        query, retrieved = await _retriever(state)
        plan = await _planner(query, retrieved, state["user_id"])
        tool_result = await _executor(plan, state["user_id"])
        final_response = await _reflector(query, tool_result, state["user_id"])
        await _memory_writer(state["user_id"], query, final_response)
    except Exception as exc:
        logger.error("okr_agent pipeline error", error=str(exc))
        final_response = f"抱歉，处理您的 OKR 请求时出现错误：{exc}"

    return Command(
        goto="supervisor",
        update={"messages": [AIMessage(content=final_response)], "current_agent": None},
    )
