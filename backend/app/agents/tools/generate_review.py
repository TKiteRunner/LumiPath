from typing import Any
from app.agents.tools.base import BaseTool, register_tool


@register_tool(name="generate_review", version="1.0.0")
class GenerateReviewTool(BaseTool):

    async def execute(self, user_id: str, **kwargs) -> dict[str, Any]:
        # TODO Step 3: 调用 LLM 生成面试复盘报告，写入 interview_reviews 表
        return {"status": "stub", "review": ""}

    @property
    def tool_schema(self) -> dict[str, Any]:
        return {
            "name": self.tool_name,
            "description": "Generate an AI interview review report for a completed interview.",
            "parameters": {
                "type": "object",
                "properties": {
                    "interview_id": {"type": "string", "description": "UUID of the interview to review"},
                },
                "required": ["interview_id"],
            },
        }
