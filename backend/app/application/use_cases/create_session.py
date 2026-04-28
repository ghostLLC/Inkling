"""创建会话用例"""
import uuid

from ai_engine.core.state_machine import SessionState
from app.domain.repositories.session_repository import SessionRepository


class CreateSessionUseCase:
    """创建写作会话"""

    def __init__(self, repo: SessionRepository):
        self.repo = repo

    def execute(self, topic: str | None = None) -> str:
        session_id = str(uuid.uuid4())[:8]
        session = SessionState(session_id=session_id)
        if topic:
            session.topic = topic
        self.repo.save(session)
        return session_id
