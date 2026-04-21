"""
Notes Agent 节点流水线。
"""
from langgraph.types import Command
from langchain_core.messages import SystemMessage

from app.agents.state import AgentState


def notes_agent(state: AgentState) -> Command[str]:
    state["messages"].append(SystemMessage(content="Notes Agent 已经处理完毕。"))
    return Command(goto="supervisor", update={"current_agent": None})
