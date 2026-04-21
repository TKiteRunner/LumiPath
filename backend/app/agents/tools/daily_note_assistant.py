from typing import Any
from app.agents.tools.base import BaseTool, register_tool


@register_tool(name="daily_note_assistant", version="1.0.0")
class DailyNoteAssistantTool(BaseTool):

    async def execute(self, user_id: str, **kwargs) -> dict[str, Any]:
        # TODO Step 3: 读取或创建今日 daily note，追加内容并写回 Vault
        return {"status": "stub"}

    @property
    def tool_schema(self) -> dict[str, Any]:
        return {
            "name": self.tool_name,
            "description": "Writes or appends content to today's daily note in the Vault.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content_to_append": {"type": "string", "description": "Markdown content to append to today's note"},
                },
                "required": ["content_to_append"],
            },
        }
