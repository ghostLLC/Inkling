"""审题立意模式处理器"""
from typing import Any

from ..state_machine import SessionState, TaskMode
from .base import ModeHandler


class TopicAnalysisHandler(ModeHandler):
    """审题立意阶段处理器"""

    @property
    def mode(self) -> TaskMode:
        return TaskMode.TOPIC_ANALYSIS

    # 完成审题的信号词
    _completion_signals = ["开始写了", "我知道了", "明白了", "懂了", "开始写", "动笔了"]

    def handle(self, session: SessionState, user_input: str) -> dict[str, Any]:
        # 1. 如果是第一轮且没题目，尝试提取
        if not session.topic and "题目" in user_input:
            session.topic = self._extract_topic(user_input)

        # 2. 检查是否完成审题
        has_completion = any(s in user_input for s in self._completion_signals)
        has_min_history = len(session.conversation_history) >= 4  # 至少4轮对话

        if has_completion and has_min_history:
            session.complete_topic_analysis()
            return {
                "ai_response": "好的，开始写吧！记住：先写出自己的想法，卡住了随时叫我。我在旁边陪写。✍️",
                "requires_llm": False,
                "transferred_to": TaskMode.STUCK_RESCUE,
                "status": "ok",
            }

        # 3. 需要 LLM 生成引导回复
        return {
            "ai_response": None,
            "requires_llm": True,
            "transferred_to": None,
            "status": "ok",
        }
