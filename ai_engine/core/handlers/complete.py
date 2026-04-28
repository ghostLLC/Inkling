"""写作完成模式处理器"""
from typing import Any

from ..state_machine import SessionState, TaskMode
from .base import ModeHandler


class CompleteHandler(ModeHandler):
    """写作完成阶段处理器"""

    @property
    def mode(self) -> TaskMode:
        return TaskMode.COMPLETE

    def handle(self, session: SessionState, user_input: str) -> dict[str, Any]:
        return {
            "ai_response": "你已经写完这篇作文了，很棒。如果想再写一篇，可以告诉我新的题目。",
            "requires_llm": False,
            "transferred_to": None,
            "status": "ok",
        }
