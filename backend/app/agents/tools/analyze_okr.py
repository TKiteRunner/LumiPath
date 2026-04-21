from typing import Any
from app.agents.tools.base import BaseTool, register_tool


@register_tool(name="analyze_okr", version="1.0.0")
class AnalyzeOKRTool(BaseTool):

    async def execute(self, user_id: str, **kwargs) -> dict[str, Any]:
        # TODO Step 3: 查询 okr_objectives / okr_key_results，计算进度差距并给出建议
        return {"status": "stub", "objectives": [], "suggestions": []}

    @property
    def tool_schema(self) -> dict[str, Any]:
        return {
            "name": self.tool_name,
            "description": "Analyze OKR progress and generate improvement suggestions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "quarter": {"type": "string", "description": "Quarter identifier, e.g. '2026-Q2'"},
                },
                "required": [],
            },
        }
