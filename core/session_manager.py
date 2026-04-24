"""
会话管理器 - 协调状态机、分类器、引导生成器和LLM
"""
import uuid
from typing import Optional, Dict, Any
from .state_machine import StateMachine, SessionState, TaskMode, GuideLevel
from .stuck_classifier import StuckClassifier
from .guide_generator import GuideGenerator
from .content_guard import ContentGuard, OutputLimiter
from .llm_provider import LLMProvider


class SessionManager:
    """
    会话管理器 - 核心协调组件
    处理用户输入，管理状态流转，生成AI回复
    """
    
    def __init__(self, llm_provider: LLMProvider):
        self.state_machine = StateMachine()
        self.classifier = StuckClassifier()
        self.guide_generator = GuideGenerator()
        self.content_guard = ContentGuard()
        self.output_limiter = OutputLimiter()
        self.llm = llm_provider
    
    def create_session(self, topic: Optional[str] = None) -> str:
        """
        创建新会话
        
        Args:
            topic: 可选的作文题目
        
        Returns:
            session_id
        """
        session_id = str(uuid.uuid4())[:8]
        session = self.state_machine.create_session(session_id)
        if topic:
            session.topic = topic
        return session_id
    
    def process(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """
        处理用户输入，返回AI回复
        
        Args:
            session_id: 会话ID
            user_input: 用户输入文本
        
        Returns:
            {
                "session_id": str,
                "task_mode": str,
                "ai_response": str,
                "current_level": int,
                "stuck_type": str,
                "cool_down": bool,
                "status": str  # "ok" / "error" / "warning"
            }
        """
        session = self.state_machine.get_session(session_id)
        if not session:
            return {
                "session_id": session_id,
                "status": "error",
                "ai_response": "会话不存在，请重新开始。"
            }
        
        # 1. 输入安全检查
        is_safe, reason = self.content_guard.check_input(user_input)
        if not is_safe:
            return {
                "session_id": session_id,
                "status": "warning",
                "ai_response": reason,
                "task_mode": session.task_mode.name,
            }
        
        # 2. 记录用户输入
        session.add_message("user", user_input)
        
        # 3. 根据当前模式处理
        try:
            if session.task_mode == TaskMode.TOPIC_ANALYSIS:
                result = self._handle_topic_analysis(session, user_input)
            elif session.task_mode == TaskMode.STUCK_RESCUE:
                result = self._handle_stuck_rescue(session, user_input)
            elif session.task_mode == TaskMode.ENDING_GUIDE:
                result = self._handle_ending_guide(session, user_input)
            elif session.task_mode == TaskMode.COMPLETE:
                result = self._handle_complete(session, user_input)
            else:
                result = self._handle_default(session, user_input)
        except Exception as e:
            return {
                "session_id": session_id,
                "status": "error",
                "ai_response": f"处理出错了，请重试。错误：{str(e)}",
                "task_mode": session.task_mode.name,
            }
        
        # 4. 输出安全检查 v2
        is_valid, processed_text, reason = self.content_guard.check_output(result["ai_response"])
        if not is_valid:
            # 严重越界：尝试让LLM重新生成
            regen_prompt = self.content_guard.get_regeneration_prompt(
                reason, 
                self.guide_generator.generate(session, user_input)
            )
            result["ai_response"] = self.llm.chat(regen_prompt["system"], regen_prompt["user"])
            # 再次检查
            is_valid2, processed_text2, reason2 = self.content_guard.check_output(result["ai_response"])
            if not is_valid2:
                # 二次失败，返回安全提示
                result["ai_response"] = "我刚才想帮你，但好像说得太多了。换个方式：你现在写到哪一步了？卡在哪里？"
                result["status"] = "warning"
            else:
                result["ai_response"] = processed_text2
        else:
            result["ai_response"] = processed_text
        
        # 5. 限制输出长度
        result["ai_response"] = self.output_limiter.limit_output(result["ai_response"])
        
        # 6. 记录AI回复
        session.add_message("assistant", result["ai_response"])
        
        # 7. 补充状态信息
        result.update({
            "session_id": session_id,
            "task_mode": session.task_mode.name,
            "current_level": session.current_level.value,
            "stuck_type": session.current_stuck_type.value if session.current_stuck_type else None,
            "cool_down": session.should_cool_down(),
        })
        
        return result
    
    def _handle_topic_analysis(self, session: SessionState, user_input: str) -> Dict[str, Any]:
        """处理审题立意阶段"""
        # 如果是第一轮，设置题目
        if not session.topic and "题目" in user_input:
            # 尝试提取题目
            if "《" in user_input and "》" in user_input:
                start = user_input.find("《") + 1
                end = user_input.find("》", start)
                session.topic = user_input[start:end]
            else:
                session.topic = user_input.strip()
        
        # 检查是否完成审题（学生说"开始写了"、"知道了"等）
        completion_signals = ["开始写了", "我知道了", "明白了", "懂了", "开始写", "动笔了"]
        if any(signal in user_input for signal in completion_signals) and len(session.conversation_history) >= 4:
            session.complete_topic_analysis()
            return {
                "ai_response": "好的，开始写吧！记住：先写出自己的想法，卡住了随时叫我。我在旁边陪写。✍️",
                "status": "ok"
            }
        
        # 生成审题Prompt并调用LLM
        prompt = self.guide_generator.generate(session, user_input)
        response = self.llm.chat(prompt["system"], prompt["user"])
        
        return {
            "ai_response": response,
            "status": "ok"
        }
    
    def _handle_stuck_rescue(self, session: SessionState, user_input: str) -> Dict[str, Any]:
        """处理卡壳救援阶段"""
        # 检查是否进入结尾阶段（只在有正文内容后才允许）
        if self.classifier._contains_any(user_input.lower(), self.classifier.ending_keywords):
            if session.has_body:
                session.start_ending_guide()
                return self._handle_ending_guide(session, user_input)
            else:
                # 正文还没写完，提醒先写完正文
                return {
                    "ai_response": "正文好像还没写完？先把中间的故事写完，我们再一起看结尾。需要我帮你推进情节吗？",
                    "status": "ok"
                }
        
        # 检查是否直接完成写作（在卡壳救援模式下）
        complete_signals = ["写完了", "完成了", "搞定了"]
        if any(signal in user_input for signal in complete_signals) and "不会" not in user_input and "怎么" not in user_input:
            session.complete_writing()
            return {
                "ai_response": "写完了？不错。先自己读一遍，看看通不通顺。如果还有时间，可以想想：开头和结尾有没有呼应？题目有没有点到位？\n\n这次写作就到这里。下次卡壳了，我还在。✍️🔥",
                "status": "ok"
            }
        
        # 更新已写内容（如果用户输入看起来像是正文内容）
        if len(user_input) > 50 and "题目" not in user_input:
            session.update_written_content(user_input)
        
        # 识别卡壳类型（如果是新的卡壳点）
        if session.stuck_count == 0 or session.current_stuck_type is None:
            stuck_type, confidence = self.classifier.classify(user_input, session.written_content)
            if stuck_type:
                session.current_stuck_type = stuck_type
                session.current_level = GuideLevel.L1_DIRECTION
                session.stuck_count = 0
        
        # 检查冷却
        if session.should_cool_down():
            # 重置层级，进入冷却模式
            session.reset_level()
            return {
                "ai_response": "💡 我们已经把这一步拆解得比较细了。现在我建议你先根据刚才的提示，自己试着写2-3句话。写完之后如果还觉得不对，我们再一起看。写作不是一次就写对的，是先写出来再改对的。✍️",
                "status": "ok"
            }
        
        # 检查学生是否说"还是不会"（推进层级）
        stuck_signals = ["还是不会", "还是不懂", "还是不知道", "还是卡", "更迷糊了", "没懂"]
        if any(signal in user_input for signal in stuck_signals):
            session.advance_level()
        
        # 生成卡壳救援Prompt并调用LLM
        prompt = self.guide_generator.generate(session, user_input)
        response = self.llm.chat(prompt["system"], prompt["user"])
        
        return {
            "ai_response": response,
            "status": "ok"
        }
    
    def _handle_ending_guide(self, session: SessionState, user_input: str) -> Dict[str, Any]:
        """处理结尾收束阶段"""
        # 更新已写内容（只在输入明显是正文内容时才更新）
        if len(user_input) > 50 and not any(keyword in user_input for keyword in ["选", "感悟", "呼应", "留白", "行动", "对话", "结尾", "策略"]):
            session.update_written_content(user_input)
        
        # 检查是否完成（必须明确说"写完了"，且不含"不会"、"怎么"等求助词）
        complete_signals = ["写完了", "完成了", "搞定了"]
        has_completion = any(signal in user_input for signal in complete_signals)
        has_help_request = any(word in user_input for word in ["不会", "怎么", "帮", "卡"])
        
        if has_completion and not has_help_request:
            session.complete_writing()
            return {
                "ai_response": "写完了？不错。先自己读一遍，看看通不通顺。如果还有时间，可以想想：开头和结尾有没有呼应？题目有没有点到位？\n\n这次写作就到这里。下次卡壳了，我还在。✍️🔥",
                "status": "ok"
            }
        
        # 生成结尾Prompt并调用LLM
        prompt = self.guide_generator.generate(session, user_input)
        response = self.llm.chat(prompt["system"], prompt["user"])
        
        return {
            "ai_response": response,
            "status": "ok"
        }
    
    def _handle_complete(self, session: SessionState, user_input: str) -> Dict[str, Any]:
        """处理写作完成后的输入"""
        return {
            "ai_response": "你已经写完这篇作文了，很棒。如果想再写一篇，可以告诉我新的题目。",
            "status": "ok"
        }
    
    def _handle_default(self, session: SessionState, user_input: str) -> Dict[str, Any]:
        """默认处理"""
        return {
            "ai_response": "我在呢。你现在写到哪一步了？卡住了吗？",
            "status": "ok"
        }
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """获取会话信息"""
        session = self.state_machine.get_session(session_id)
        if not session:
            return None
        return session.to_dict()
    
    def set_topic(self, session_id: str, topic: str) -> bool:
        """手动设置作文题目"""
        session = self.state_machine.get_session(session_id)
        if not session:
            return False
        session.topic = topic
        return True
