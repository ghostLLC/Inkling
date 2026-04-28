"""
统一日志配置
"""
import logging
import sys
from typing import Optional


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
) -> None:
    """
    配置应用日志
    
    输出到 stdout，便于容器环境收集
    """
    if format_string is None:
        format_string = (
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(format_string))

    # 根日志器
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers = [handler]

    # 抑制第三方库的冗余日志
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Inkling 模块日志级别
    logging.getLogger("ai_engine").setLevel(logging.DEBUG)
    logging.getLogger("app").setLevel(logging.DEBUG)


def get_logger(name: str) -> logging.Logger:
    """获取命名日志器"""
    return logging.getLogger(name)
