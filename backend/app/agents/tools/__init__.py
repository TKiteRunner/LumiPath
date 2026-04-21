"""
Tools package — importing all tool modules triggers @register_tool decorators.
"""
from app.agents.tools.base import BaseTool, register_tool, TOOL_REGISTRY

from app.agents.tools import search_questions  # noqa: F401
from app.agents.tools import generate_review  # noqa: F401
from app.agents.tools import daily_note_assistant  # noqa: F401
from app.agents.tools import analyze_status  # noqa: F401
from app.agents.tools import analyze_okr  # noqa: F401
from app.agents.tools import suggest_tasks  # noqa: F401
from app.agents.tools import generate_report  # noqa: F401
from app.agents.tools import search_notes  # noqa: F401
from app.agents.tools import create_summary  # noqa: F401

__all__ = ["BaseTool", "register_tool", "TOOL_REGISTRY"]
