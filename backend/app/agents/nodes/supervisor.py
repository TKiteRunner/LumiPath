"""
Supervisor Agent 节点：负责意图分类与分发路由。
"""
from langgraph.types import Command
from langchain_core.messages import SystemMessage

from app.agents.state import AgentState


def supervisor_agent(state: AgentState) -> Command[str]:
    """
    根据上文及最后一条用户 query，判断应该路由到哪个 Specialized Agent。
    如果没有匹配的特定需求，则响应用户。
    """
    # TODO Step 3:
    # prompt = PromptTemplate.from_template("Classify intent: interview, okr, notes, memory, END. User said: {message}")
    # llm_result = llm.invoke(...)
    
    # Stub logic (硬编码路由)
    last_msg = state["messages"][-1].content.lower() if state["messages"] else ""
    target = "END"
    
    if "interview" in last_msg or "面试" in last_msg:
        target = "interview_agent"
    elif "okr" in last_msg or "目标" in last_msg:
        target = "okr_agent"
    elif "note" in last_msg or "笔记" in last_msg:
        target = "notes_agent"
    elif "记忆" in last_msg or "记住" in last_msg:
        target = "memory_agent"
    
    if target == "END":
        return Command(
            goto="__end__",
            update={"messages": [SystemMessage(content="Supervisor 无法识别特定意图，直接响应。")]},
        )
    else:
        return Command(goto=target, update={"next_agent": target, "current_agent": target})
