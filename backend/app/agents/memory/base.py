"""
7层记忆接口与基类定义。
"""
from abc import ABC, abstractmethod
from typing import Any


class BaseMemory(ABC):
    """Memory 层的抽象基类。"""

    def __init__(self, user_id: str):
        self.user_id = user_id

    @abstractmethod
    async def read(self, key: str, **kwargs) -> Any:
        """精确读取。"""
        pass

    @abstractmethod
    async def write(self, data: Any, **kwargs) -> None:
        """写入/更新。"""
        pass

    @abstractmethod
    async def search(self, query: str, top_k: int = 5, **kwargs) -> list[dict]:
        """模糊/语义检索。"""
        pass
