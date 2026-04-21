"""
Tool 基础抽象类和注册器。
BaseTool / @register_tool / TOOL_REGISTRY
"""
from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """
    Tool 基类。所有 Agent 动作均通过 Tool 执行，
    便于挂载 MCP 暴露和记录 ProceduralMemory。
    """
    tool_name: str = ""
    tool_version: str = "1.0.0"

    @abstractmethod
    async def execute(self, user_id: str, **kwargs) -> dict[str, Any]:
        """执行该 Tool 的核心逻辑，返回结构化结果。"""

    @property
    @abstractmethod
    def tool_schema(self) -> dict[str, Any]:
        """返回符合 OpenAI Function Calling / LangChain Tool 的 JSON Schema。"""


TOOL_REGISTRY: dict[str, type[BaseTool]] = {}


def register_tool(name: str, version: str = "1.0.0"):
    """
    装饰器：把被装饰的 Tool 类注册到 TOOL_REGISTRY。

    用法：
        @register_tool(name="search_questions", version="1.0.0")
        class SearchQuestionsTool(BaseTool): ...
    """
    def decorator(cls: type[BaseTool]) -> type[BaseTool]:
        cls.tool_name = name
        cls.tool_version = version
        TOOL_REGISTRY[name] = cls
        return cls
    return decorator
