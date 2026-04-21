from typing import Any
from app.agents.tools.base import BaseTool, register_tool


@register_tool(name="suggest_tasks", version="1.0.0")
class SuggestTasksTool(BaseTool):

    async def execute(self, user_id: str, **kwargs) -> dict[str, Any]:
        # TODO Step 3: 根据 OKR 进度和历史 daily_tasks 智能推荐今日任务
        return {"status": "stub", "tasks": []}

    @property
    def tool_schema(self) -> dict[str, Any]:
        return {
            "name": self.tool_name,
            "description": "Suggest daily tasks based on OKR progress and past patterns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Target date in YYYY-MM-DD format"},
                    "max_tasks": {"type": "integer", "default": 5},
                },
                "required": [],
            },
        }
