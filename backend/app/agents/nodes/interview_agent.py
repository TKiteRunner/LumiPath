"""
Interview Agent 节点流水线。
内部应包含：retriever -> planner -> executor -> reflector -> memory_writer
这里使用简化的单节点作为封装，最终发 Command 回到 supervisor。
"""
from langgraph.types import Command
from langchain_core.messages import SystemMessage

from app.agents.state import AgentState


def interview_agent(state: AgentState) -> Command[str]:
    """
    面试复盘专家 Agent。
    """
    # ...TODO: retriever -> planner -> executor -> reflector -> memory_writer
    
    state["messages"].append(SystemMessage(content="Interview Agent 已经处理完毕。"))
    
    # 处理完后，交回 supervisor 处理（可以 resume 并等待用户下一句话，或者直接结束）
    return Command(goto="supervisor", update={"current_agent": None})
