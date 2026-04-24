"""SQLAlchemy 会话仓储实现"""
from typing import Optional, List

from sqlalchemy.orm import Session

from app.infrastructure.db.models import SessionORM, MessageORM
from app.domain.repositories.session_repository import SessionRepository
from core.state_machine import SessionState, TaskMode, GuideLevel, StuckType


class SQLAlchemySessionRepository(SessionRepository):
    """基于 SQLAlchemy 的会话仓储"""

    def __init__(self, db: Session):
        self.db = db

    def _to_state(self, orm: SessionORM) -> SessionState:
        """ORM -> 领域对象"""
        state = SessionState(session_id=orm.id)
        state.topic = orm.topic or ""
        state.task_mode = TaskMode[orm.task_mode] if orm.task_mode in TaskMode.__members__ else TaskMode.TOPIC_ANALYSIS
        state.current_level = GuideLevel(orm.current_level) if orm.current_level else GuideLevel.L1_DIRECTION
        state.stuck_count = orm.stuck_count or 0
        state.topic_analysis_complete = orm.topic_analysis_complete or False
        state.has_body = orm.has_body or False
        state.written_content = orm.written_content or ""
        if orm.stuck_type and orm.stuck_type in StuckType.__members__:
            state.current_stuck_type = StuckType[orm.stuck_type]
        return state

    def _to_orm(self, state: SessionState) -> SessionORM:
        """领域对象 -> ORM（用于更新）"""
        return SessionORM(
            id=state.session_id,
            topic=state.topic or None,
            task_mode=state.task_mode.name,
            current_level=state.current_level.value if state.current_level else 1,
            stuck_type=state.current_stuck_type.name if state.current_stuck_type else None,
            stuck_count=state.stuck_count,
            topic_analysis_complete=state.topic_analysis_complete,
            has_body=state.has_body,
            written_content=state.written_content,
        )

    def save(self, session: SessionState) -> None:
        """保存/更新会话"""
        orm = self.db.query(SessionORM).filter(SessionORM.id == session.session_id).first()
        if orm:
            # 更新
            orm.topic = session.topic or None
            orm.task_mode = session.task_mode.name
            orm.current_level = session.current_level.value if session.current_level else 1
            orm.stuck_type = session.current_stuck_type.name if session.current_stuck_type else None
            orm.stuck_count = session.stuck_count
            orm.topic_analysis_complete = session.topic_analysis_complete
            orm.has_body = session.has_body
            orm.written_content = session.written_content
        else:
            # 新建
            orm = self._to_orm(session)
            self.db.add(orm)
        self.db.commit()

    def get_by_id(self, session_id: str) -> Optional[SessionState]:
        """按 ID 查询"""
        orm = self.db.query(SessionORM).filter(SessionORM.id == session_id).first()
        if not orm:
            return None
        return self._to_state(orm)

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """添加消息记录"""
        msg = MessageORM(session_id=session_id, role=role, content=content)
        self.db.add(msg)
        self.db.commit()

    def get_messages(self, session_id: str) -> List[dict]:
        """获取会话消息历史"""
        msgs = self.db.query(MessageORM).filter(MessageORM.session_id == session_id).order_by(MessageORM.created_at).all()
        return [{"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()} for m in msgs]
