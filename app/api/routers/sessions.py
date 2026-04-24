"""会话路由 - 核心 API"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.infrastructure.db.base import get_db
from app.infrastructure.config.settings import get_settings
from app.infrastructure.repositories.sqlalchemy_session_repository import SQLAlchemySessionRepository
from app.domain.repositories.session_repository import SessionRepository
from app.application.use_cases.create_session import CreateSessionUseCase
from app.application.use_cases.process_message import ProcessMessageUseCase
from app.application.use_cases.get_session_info import GetSessionInfoUseCase

router = APIRouter(prefix="/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    topic: Optional[str] = None


class MessageRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    task_mode: str
    ai_response: str
    current_level: int
    stuck_type: Optional[str]
    cool_down: bool
    status: str


class SessionInfoResponse(BaseModel):
    session_id: str
    topic: Optional[str]
    task_mode: str
    current_level: int
    stuck_count: int
    cool_down: bool
    messages: list


# === 依赖注入 ===

def get_repo(db: Session = Depends(get_db)) -> SessionRepository:
    return SQLAlchemySessionRepository(db)


def get_llm_provider():
    settings = get_settings()
    from core.llm_provider import create_provider
    if settings.is_mock:
        return create_provider("mock")
    return create_provider(
        settings.provider_type,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        base_url=settings.llm_base_url,
    )


# === 端点 ===

@router.post("", response_model=dict)
async def create_session(
    req: CreateSessionRequest,
    repo: SessionRepository = Depends(get_repo),
):
    """创建新会话"""
    use_case = CreateSessionUseCase(repo)
    session_id = use_case.execute(req.topic)
    return {"session_id": session_id, "status": "created"}


@router.post("/{session_id}/messages", response_model=ChatResponse)
async def send_message(
    session_id: str,
    req: MessageRequest,
    repo: SessionRepository = Depends(get_repo),
    llm_provider=Depends(get_llm_provider),
):
    """发送消息并获取 AI 回复"""
    use_case = ProcessMessageUseCase(repo, llm_provider)
    result = use_case.execute(session_id, req.message)
    return ChatResponse(**result)


@router.get("/{session_id}", response_model=SessionInfoResponse)
async def get_session(
    session_id: str,
    repo: SessionRepository = Depends(get_repo),
):
    """获取会话信息"""
    use_case = GetSessionInfoUseCase(repo)
    info = use_case.execute(session_id)
    if not info:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionInfoResponse(**info)
