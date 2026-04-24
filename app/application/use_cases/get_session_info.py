"""获取会话信息用例"""
from typing import Optional, Dict, Any

from app.domain.repositories.session_repository import SessionRepository


class GetSessionInfoUseCase:
    """查询会话当前状态和历史"""

    def __init__(self, repo: SessionRepository):
        self.repo = repo

    def execute(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self.repo.get_by_id(session_id)
        if not session:
            return None

        messages = self.repo.get_messages(session_id)

        return {
            "session_id": session.session_id,
            "topic": session.topic or None,
            "task_mode": session.task_mode.name,
            "current_level": session.current_level.value if session.current_level else 1,
            "stuck_count": session.stuck_count,
            "cool_down": session.should_cool_down(),
            "messages": messages,
        }
