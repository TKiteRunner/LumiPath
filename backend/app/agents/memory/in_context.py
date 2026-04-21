"""
In-Context Memory (实际上就是和 State Dictionary 交互的方法包装)
"""
from typing import Any

from app.agents.state import AgentState
from app.agents.memory.base import BaseMemory


class InContextMemory(BaseMemory):
    def __init__(self, user_id: str, state: AgentState):
        super().__init__(user_id)
        self.state = state

    async def read(self, key: str, **kwargs) -> Any:
        return self.state.get(key)

    async def write(self, data: dict, **kwargs) -> None:
        """不支持直接 update 全局 state（违反 LangGraph 原则），只允许更新 scratchpad。"""
        if "scratchpad" not in self.state:
            self.state["scratchpad"] = {}
        self.state["scratchpad"].update(data)

    async def search(self, query: str, top_k: int = 5, **kwargs) -> list[dict]:
        # 工作记忆不提供搜索，直接看 state.messages
        return []
