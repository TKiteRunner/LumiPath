from typing import Any
from app.agents.tools.base import BaseTool, register_tool


@register_tool(name="search_questions", version="1.0.0")
class SearchQuestionsTool(BaseTool):

    async def execute(self, user_id: str, **kwargs) -> dict[str, Any]:
        return {"status": "success", "result": "stub results"}

    @property
    def tool_schema(self) -> dict[str, Any]:
        return {
            "name": self.tool_name,
            "description": "Search interview questions in database",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                },
                "required": ["query"],
            },
        }
