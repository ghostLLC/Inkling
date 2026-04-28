"""会话管理器 - 协调层（重构版）

职责（更薄）：
1. 创建/获取会话
2. 协调安全检查 → 模式分发 → LLM编排 → 记录

业务逻辑已下沉到：
- core/handlers/   - 模式处理器
- core/pipeline/   - 安全流水线 + LLM编排器
"""
import uuid
from typing import Any

from .content_guard import ContentGuard
from .guide_generator import GuideGenerator
from .handlers.complete import CompleteHandler
from .handlers.ending_guide import EndingGuideHandler
from .handlers.stuck_rescue import StuckRescueHandler
from .handlers.topic_analysis import TopicAnalysisHandler
from .llm_provider import LLMProvider
from .pipeline import LLMOrchestrator, SecurityPipeline
from .state_machine import SessionState, StateMachine, TaskMode
from .stuck_classifier import StuckClassifier


class SessionManager:
    """会话管理器 - 精简协调组件"""

    def __init__(self, llm_provider: LLMProvider):
        self.state_machine = StateMachine()
        self.guide_generator = GuideGenerator()
        self.content_guard = ContentGuard()
        self.llm = llm_provider

        # Pipeline 组件
        self.security = SecurityPipeline(self.content_guard, self.llm)
        self.orchestrator = LLMOrchestrator(
            self.guide_generator, self.security, self.llm
        )

        # 初始化模式处理器
        classifier = StuckClassifier()
        self._handlers = {
            TaskMode.TOPIC_ANALYSIS: TopicAnalysisHandler(),
            TaskMode.STUCK_RESCUE: StuckRescueHandler(classifier),
            TaskMode.ENDING_GUIDE: EndingGuideHandler(),
            TaskMode.COMPLETE: CompleteHandler(),
        }

    def create_session(self, topic: str | None = None) -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())[:8]
        session = self.state_machine.create_session(session_id)
        if topic:
            session.topic = topic
        return session_id

    def process(self, session_id: str, user_input: str) -> dict[str, Any]:
        """处理用户输入，返回AI回复

        流程：安全检查 → 模式分发 → Handler处理 → LLM编排 → 记录
        """
        session = self.state_machine.get_session(session_id)
        if not session:
            return {
                "session_id": session_id,
                "status": "error",
                "ai_response": "会话不存在，请重新开始。",
            }

        # 1. 输入安全检查
        is_safe, reason = self.security.check_input(user_input)
        if not is_safe:
            return self._build_result(
                session, session_id,
                ai_response=reason,
                status="warning",
            )

        # 2. 记录用户输入
        session.add_message("user", user_input)

        # 3. 模式分发 → Handler 处理
        try:
            handler = self._handlers.get(session.task_mode)
            if handler is None:
                result = self._handle_unknown_mode(session, user_input)
            else:
                handler_result = handler.handle(session, user_input)
                result = self._process_handler_result(
                    session, session_id, user_input, handler_result
                )
        except Exception as e:
            return self._build_result(
                session, session_id,
                ai_response=f"处理出错了，请重试。错误：{str(e)}",
                status="error",
            )

        # 4. 记录AI回复（如果成功）
        if result.get("status") in ("ok", "warning"):
            session.add_message("assistant", result["ai_response"])

        return result

    def _process_handler_result(
        self,
        session: SessionState,
        session_id: str,
        user_input: str,
        handler_result: dict[str, Any],
    ) -> dict[str, Any]:
        """处理 Handler 返回结果"""
        # 如果 Handler 已经提供了固定回复，直接返回
        if not handler_result.get("requires_llm", False):
            return self._build_result(
                session, session_id,
                ai_response=handler_result["ai_response"],
                status=handler_result.get("status", "ok"),
                cool_down=handler_result.get("cool_down", False),
            )

        # 需要 LLM 生成回复 → 委托给编排器
        llm_result = self.orchestrator.generate_response(session, user_input)
        return self._build_result(
            session, session_id,
            ai_response=llm_result["ai_response"],
            status=llm_result["status"],
        )

    def _handle_unknown_mode(self, session: SessionState, user_input: str) -> dict[str, Any]:
        """处理未知模式"""
        return self._build_result(
            session, session.session_id,
            ai_response="我在呢。你现在写到哪一步了？卡住了吗？",
            status="ok",
        )

    def _build_result(
        self,
        session: SessionState,
        session_id: str,
        ai_response: str,
        status: str,
        cool_down: bool | None = None,
    ) -> dict[str, Any]:
        """构建统一返回格式"""
        return {
            "session_id": session_id,
            "task_mode": session.task_mode.name,
            "ai_response": ai_response,
            "current_level": session.current_level.value if session.current_level else 1,
            "stuck_type": session.current_stuck_type.value if session.current_stuck_type else None,
            "cool_down": cool_down if cool_down is not None else session.should_cool_down(),
            "status": status,
        }

    def get_session_info(self, session_id: str) -> dict | None:
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
