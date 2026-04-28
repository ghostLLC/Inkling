"""健康检查路由"""
from fastapi import APIRouter

from app.infrastructure.config.settings import get_settings
from app.infrastructure.logging import get_logger

router = APIRouter(tags=["health"])
logger = get_logger("app.health")


@router.get("/health")
async def health_check():
    """健康检查"""
    settings = get_settings()
    logger.debug("Health check requested")
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": "0.2.0",
        "provider_type": settings.provider_type,
        "has_llm_config": settings.has_llm_config,
    }
