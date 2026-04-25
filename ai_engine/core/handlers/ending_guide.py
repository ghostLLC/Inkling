"""结尾收束模式处理器"""
from typing import Dict, Any

from ..state_machine import SessionState, TaskMode
from .base import ModeHandler


class EndingGuideHandler(ModeHandler):
    """结尾收束阶段处理器"""
    
    @property
    def mode(self) -> TaskMode:
        return TaskMode.ENDING_GUIDE
    
    # 完成信号词
    _complete_signals = ["写完了", "完成了", "搞定了"]
    # 求助词（排除误触）
    _help_words = ["不会", "怎么", "帮", "卡"]
    # 策略关键词（用于区分正文内容）
    _strategy_keywords = ["选", "感悟", "呼应", "留白", "行动", "对话", "结尾", "策略"]
    
    def handle(self, session: SessionState, user_input: str) -> Dict[str, Any]:
        # 1. 更新已写内容（长文本且不含策略关键词）
        if len(user_input) > 50 and not any(kw in user_input for kw in self._strategy_keywords):
            session.update_written_content(user_input)
        
        # 2. 检查是否完成
        if self._is_complete_signal(user_input):
            session.complete_writing()
            return {
                "ai_response": "写完了？不错。先自己读一遍，看看通不通顺。如果还有时间，可以想想：开头和结尾有没有呼应？题目有没有点到位？\n\n这次写作就到这里。下次卡壳了，我还在。✍️🔥",
                "requires_llm": False,
                "transferred_to": TaskMode.COMPLETE,
                "status": "ok",
            }
        
        # 3. 需要 LLM 生成引导回复
        return {
            "ai_response": None,
            "requires_llm": True,
            "transferred_to": None,
            "status": "ok",
        }
    
    def _is_complete_signal(self, user_input: str) -> bool:
        """判断用户是否表示写作完成"""
        has_signal = any(s in user_input for s in self._complete_signals)
        has_help = any(w in user_input for w in self._help_words)
        return has_signal and not has_help
