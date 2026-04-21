"""
Tool 基础抽象类和注册器。
"""
from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """
    Tool 基类，所有的代理动作均通过 Tool 执行，便于挂载 MCP 和记录 Procedural Memory。
    """
    tool_name: str
    tool_version: str

    @abstractmethod
    async def execute(self, user_id: str, **kwargs) -> dict[str, Any]:
        """执行该技能的核心逻辑。"""
        pass

    @property
    @abstractmethod
    def tool_schema(self) -> dict[str, Any]:
        """返回符合 OpenAI Function Calling / LangChain Tool 的 Schema。"""
        pass


TOOL_REGISTRY: dict[str, type[BaseTool]] = {}


def register_tool(name: str, version: str = "1.0.0"):
    """
    注册器装饰器：把被装饰的类注册到 TOOL_REGISTRY 中。
    """
    def decorator(cls: type[BaseTool]) -> type[BaseTool]:
        cls.tool_name = name
        cls.tool_version = version
        TOOL_REGISTRY[name] = cls
        return cls

    return decorator
