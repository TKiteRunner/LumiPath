from typing import Any
from app.agents.tools.base import BaseTool, register_tool


@register_tool(name="daily_note_assistant", version="1.0.0")
class DailyNoteAssistantTool(BaseTool):

    async def execute(self, user_id: str, **kwargs) -> dict[str, Any]:
        return {"status": "success"}

    @property
    def tool_schema(self) -> dict[str, Any]:
        return {
            "name": self.tool_name,
            "description": "Writes or updates today's daily note.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content_to_append": {"type": "string"},
                },
                "required": ["content_to_append"],
            },
        }
