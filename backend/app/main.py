"""FastAPI 应用入口"""
import sys
import os

# 将项目根目录加入 sys.path，使 from ai_engine.core.xxx 可解析
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.infrastructure.db.base import init_db
from app.infrastructure.config.settings import get_settings
from app.infrastructure.logging import setup_logging, get_logger
from app.api.routers import health, sessions, enhanced

settings = get_settings()
logger = get_logger("app.main")

# 启动时初始化日志
setup_logging(level="DEBUG" if settings.debug else "INFO")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    logger.info("🚀 Inkling 启动中...")
    # 启动时初始化数据库
    init_db()
    logger.info("✅ 数据库初始化完成")
    yield
    # 关闭时清理
    logger.info("🛑 Inkling 关闭")


app = FastAPI(
    title="Inkling - AI 写作卡壳救援助手",
    description="初中生记叙文写作过程型辅导 API",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由
app.include_router(health.router)
app.include_router(sessions.router, prefix="/api")
app.include_router(enhanced.router, prefix="/api")

# 静态文件（前端页面）
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
frontend_dir = os.path.join(project_root, "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")
    logger.info(f"📁 前端目录挂载: {frontend_dir}")
