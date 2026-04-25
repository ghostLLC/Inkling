"""会话仓储接口（领域层）"""
from abc import ABC, abstractmethod
from typing import Optional, List

from ai_engine.core.state_machine import SessionState


class SessionRepository(ABC):
    """会话仓储抽象"""

    @abstractmethod
    def save(self, session: SessionState) -> None:
        """保存会话"""
        pass

    @abstractmethod
    def get_by_id(self, session_id: str) -> Optional[SessionState]:
        """按 ID 查询"""
        pass

    @abstractmethod
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """添加消息记录"""
        pass

    @abstractmethod
    def get_messages(self, session_id: str) -> List[dict]:
        """获取会话消息历史"""
        pass
