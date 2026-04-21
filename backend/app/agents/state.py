"""
LangGraph State Definition.
"""
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    单次 LangGraph 执行的全局状态字典。
    """
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    session_id: str
    scratchpad: dict         # 存放中间推理数据 / tools call 的临时结果
    retrieved: dict          # RRF 融合后召回的各层记忆
    token_budget: int
    next_agent: str | None   # Supervisor 决定路由到哪个下级 Agent
    current_agent: str | None # 当前正在执行的 specialized agent

def create_initial_state(user_id: str, session_id: str) -> AgentState:
    return {
        "messages": [],
        "user_id": user_id,
        "session_id": session_id,
        "scratchpad": {},
        "retrieved": {},
        "token_budget": 100000,
        "next_agent": None,
        "current_agent": None,
    }
