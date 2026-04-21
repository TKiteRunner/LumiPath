from typing import Any
from app.agents.tools.base import BaseTool, register_tool


@register_tool(name="generate_review", version="1.0.0")
class GenerateReviewTool(BaseTool):

    async def execute(self, user_id: str, **kwargs) -> dict[str, Any]:
        return {"status": "success"}

    @property
    def tool_schema(self) -> dict[str, Any]:
        return {
            "name": self.tool_name,
            "description": "Generate an interview review report.",
            "parameters": {
                "type": "object",
                "properties": {
                    "interview_id": {"type": "string"},
                },
                "required": ["interview_id"],
            },
        }
