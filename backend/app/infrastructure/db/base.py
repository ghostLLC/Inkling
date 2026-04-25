"""数据库连接与基类"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.infrastructure.config.settings import get_settings

Base = declarative_base()

# 全局引擎和 Session 工厂（延迟初始化，支持测试覆盖）
_engine = None
_SessionLocal = None


def get_engine():
    """获取或创建数据库引擎（支持配置变更后重新创建）"""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
            echo=settings.debug,
        )
    return _engine


def reset_engine():
    """重置引擎（测试用）"""
    global _engine, _SessionLocal
    _engine = None
    _SessionLocal = None


def get_session_local():
    """获取或创建 Session 工厂"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def get_db():
    """FastAPI 依赖：获取数据库 session"""
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """初始化数据库（创建所有表）"""
    Base.metadata.create_all(bind=get_engine())
