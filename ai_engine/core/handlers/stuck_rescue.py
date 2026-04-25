"""卡壳救援模式处理器"""
from typing import Dict, Any, Optional

from ..state_machine import SessionState, TaskMode, GuideLevel
from ..stuck_classifier import StuckClassifier
from .base import ModeHandler


class StuckRescueHandler(ModeHandler):
    """卡壳救援阶段处理器"""
    
    @property
    def mode(self) -> TaskMode:
        return TaskMode.STUCK_RESCUE
    
    def __init__(self, classifier: Optional[StuckClassifier] = None):
        self.classifier = classifier or StuckClassifier()
    
    # 完成写作的信号词
    _complete_signals = ["写完了", "完成了", "搞定了"]
    # 求助词（排除误触完成）
    _help_words = ["不会", "怎么"]
    # 层级推进信号
    _stuck_signals = ["还是不会", "还是不懂", "还是不知道", "还是卡", "更迷糊了", "没懂"]
    
    def handle(self, session: SessionState, user_input: str) -> Dict[str, Any]:
        # 1. 检查是否进入结尾阶段（正文写完后）
        if self._is_ending_request(user_input):
            if session.has_body:
                session.start_ending_guide()
                return {
                    "ai_response": None,
                    "requires_llm": True,
                    "transferred_to": TaskMode.ENDING_GUIDE,
                    "status": "ok",
                }
            else:
                return {
                    "ai_response": "正文好像还没写完？先把中间的故事写完，我们再一起看结尾。需要我帮你推进情节吗？",
                    "requires_llm": False,
                    "transferred_to": None,
                    "status": "ok",
                }
        
        # 2. 检查是否直接完成写作
        if self._is_complete_signal(user_input):
            session.complete_writing()
            return {
                "ai_response": "写完了？不错。先自己读一遍，看看通不通顺。如果还有时间，可以想想：开头和结尾有没有呼应？题目有没有点到位？\n\n这次写作就到这里。下次卡壳了，我还在。✍️🔥",
                "requires_llm": False,
                "transferred_to": TaskMode.COMPLETE,
                "status": "ok",
            }
        
        # 3. 更新已写内容（长文本 + 不含"题目"）
        if len(user_input) > 50 and "题目" not in user_input:
            session.update_written_content(user_input)
        
        # 4. 识别卡壳类型（新卡点）
        self._classify_if_new(session, user_input)
        
        # 5. 检查冷却
        if session.should_cool_down():
            session.reset_level()
            return {
                "ai_response": "💡 我们已经把这一步拆解得比较细了。现在我建议你先根据刚才的提示，自己试着写2-3句话。写完之后如果还觉得不对，我们再一起看。写作不是一次就写对的，是先写出来再改对的。✍️",
                "requires_llm": False,
                "transferred_to": None,
                "cool_down": True,
                "status": "ok",
            }
        
        # 6. 检查层级推进
        if any(s in user_input for s in self._stuck_signals):
            session.advance_level()
        
        # 7. 需要 LLM 生成引导回复
        return {
            "ai_response": None,
            "requires_llm": True,
            "transferred_to": None,
            "status": "ok",
        }
    
    def _is_ending_request(self, user_input: str) -> bool:
        """判断用户是否想进入结尾阶段"""
        return self.classifier._contains_any(
            user_input.lower(),
            self.classifier.ending_keywords
        )
    
    def _is_complete_signal(self, user_input: str) -> bool:
        """判断用户是否表示写作完成"""
        has_signal = any(s in user_input for s in self._complete_signals)
        has_help = any(w in user_input for w in self._help_words)
        return has_signal and not has_help
    
    def _classify_if_new(self, session: SessionState, user_input: str) -> None:
        """如果是新卡壳点，识别类型"""
        if session.stuck_count == 0 or session.current_stuck_type is None:
            stuck_type, _ = self.classifier.classify(user_input, session.written_content)
            if stuck_type:
                session.current_stuck_type = stuck_type
                session.current_level = GuideLevel.L1_DIRECTION
                session.stuck_count = 0
