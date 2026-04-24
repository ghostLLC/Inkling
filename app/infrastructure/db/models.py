"""数据库 ORM 模型"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean

from app.infrastructure.db.base import Base


class SessionORM(Base):
    """会话 ORM 模型"""
    __tablename__ = "sessions"

    id = Column(String(16), primary_key=True, index=True)
    topic = Column(String(255), nullable=True)
    task_mode = Column(String(32), default="TOPIC_ANALYSIS")
    current_level = Column(Integer, default=1)
    stuck_type = Column(String(32), nullable=True)
    stuck_count = Column(Integer, default=0)
    topic_analysis_complete = Column(Boolean, default=False)
    has_body = Column(Boolean, default=False)
    written_content = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MessageORM(Base):
    """消息 ORM 模型"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(16), index=True, nullable=False)
    role = Column(String(16), nullable=False)  # user / assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
