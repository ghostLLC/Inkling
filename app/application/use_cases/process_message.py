"""处理用户消息用例"""
from typing import Dict, Any

from app.domain.repositories.session_repository import SessionRepository
from core import SessionManager
from core.llm_provider import LLMProvider


class ProcessMessageUseCase:
    """处理用户消息 - 核心主用例"""

    def __init__(self, repo: SessionRepository, llm_provider: LLMProvider):
        self.repo = repo
        self.llm = llm_provider
        # SessionManager 内部包含状态机、分类器、生成器等
        self.manager = SessionManager(llm_provider)

    def execute(self, session_id: str, message: str) -> Dict[str, Any]:
        # 1. 从数据库加载会话状态
        session = self.repo.get_by_id(session_id)
        if not session:
            return {
                "session_id": session_id,
                "status": "error",
                "ai_response": "会话不存在，请重新开始。",
                "task_mode": "ERROR",
                "current_level": 0,
                "stuck_type": None,
                "cool_down": False,
            }

        # 2. 将状态注入 SessionManager 的内部状态机
        self.manager.state_machine.sessions[session_id] = session

        # 3. 处理消息
        result = self.manager.process(session_id, message)

        # 4. 保存更新后的状态
        updated_session = self.manager.state_machine.get_session(session_id)
        if updated_session:
            self.repo.save(updated_session)
            # 记录消息
            self.repo.add_message(session_id, "user", message)
            self.repo.add_message(session_id, "assistant", result["ai_response"])

        return result
