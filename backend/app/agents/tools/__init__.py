from app.agents.tools.base import BaseTool, TOOL_REGISTRY, register_tool

# 需要引入所有的 tool 模块，保证装饰器被执行，完成注册
from app.agents.tools.search_questions import SearchQuestionsTool
from app.agents.tools.generate_review import GenerateReviewTool
from app.agents.tools.daily_note_assistant import DailyNoteAssistantTool

__all__ = ["BaseTool", "TOOL_REGISTRY", "register_tool"]
