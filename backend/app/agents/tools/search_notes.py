from typing import Any
from app.agents.tools.base import BaseTool, register_tool


@register_tool(name="search_notes", version="1.0.0")
class SearchNotesTool(BaseTool):

    async def execute(self, user_id: str, **kwargs) -> dict[str, Any]:
        # TODO Step 3: 查询 notes 表，支持全文 + 向量检索
        return {"status": "stub", "results": []}

    @property
    def tool_schema(self) -> dict[str, Any]:
        return {
            "name": self.tool_name,
            "description": "Search personal notes by keyword or semantic similarity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "note_type": {"type": "string", "description": "Filter by note type (daily/weekly/interview/okr/free)"},
                    "top_k": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        }
