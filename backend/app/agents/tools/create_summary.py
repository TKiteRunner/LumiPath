from typing import Any
from app.agents.tools.base import BaseTool, register_tool


@register_tool(name="create_summary", version="1.0.0")
class CreateSummaryTool(BaseTool):

    async def execute(self, user_id: str, **kwargs) -> dict[str, Any]:
        # TODO Step 3: 对指定内容调用 LLM 生成压缩摘要，写入 memory_summaries
        return {"status": "stub", "summary": ""}

    @property
    def tool_schema(self) -> dict[str, Any]:
        return {
            "name": self.tool_name,
            "description": "Summarize a conversation or document and store in memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Text to summarize"},
                    "source_type": {"type": "string", "description": "Source type: conversation/interview/weekly/monthly", "default": "conversation"},
                    "source_id": {"type": "string", "description": "Optional UUID of the source record"},
                },
                "required": ["content"],
            },
        }
