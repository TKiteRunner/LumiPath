"""
LangGraph 主图拼接：Supervisor + 4 个 Specialized Agents
"""
from langgraph.graph import StateGraph, START, END

from app.agents.state import AgentState
from app.agents.nodes.supervisor import supervisor_agent
from app.agents.nodes.interview_agent import interview_agent
from app.agents.nodes.okr_agent import okr_agent
from app.agents.nodes.notes_agent import notes_agent
from app.agents.nodes.memory_agent import memory_agent

# 构建图
graph_builder = StateGraph(AgentState)

# 注册节点
graph_builder.add_node("supervisor", supervisor_agent)
graph_builder.add_node("interview_agent", interview_agent)
graph_builder.add_node("okr_agent", okr_agent)
graph_builder.add_node("notes_agent", notes_agent)
graph_builder.add_node("memory_agent", memory_agent)

# 指定起始节点
graph_builder.add_edge(START, "supervisor")

# 节点返回 Command 已经内置了路由，无需手动配置所有的 edge:
# 比如 interview_agent 返回 Command(goto="supervisor") 自动会有那条线。

# 编译成可运行对象
compiled_graph = graph_builder.compile()

if __name__ == "__main__":
    print(compiled_graph.get_graph().draw_ascii())
