"""
增强功能路由 - 五大模块 API
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ai_engine.core.content_analyzer import ContentAnalyzer
from ai_engine.core.progress_tracker import ProgressTracker
from ai_engine.core.emotion_engine import EmotionEngine, EmotionLevel
from ai_engine.core.training_deck import TrainingDeck
from ai_engine.core.review_generator import ReviewGenerator, WritingSession, StuckRecord

router = APIRouter(prefix="/enhanced", tags=["enhanced"])

# === 全局实例 ===
content_analyzer = ContentAnalyzer()
training_deck = TrainingDeck()
review_generator = ReviewGenerator()

# 内存存储
progress_trackers: dict = {}
emotion_engines: dict = {}
session_writing_sessions: dict = {}


# === 数据模型 ===

class AnalyzeRequest(BaseModel):
    text: str
    cursor_pos: Optional[int] = None


class AnalyzeResponse(BaseModel):
    stuck_type: Optional[str]
    stuck_confidence: float
    section: str
    section_progress: float
    word_count: int
    paragraph_count: int
    content_density: dict
    emotion_signals: List[dict]
    suggestions: List[str]


class ProgressResponse(BaseModel):
    sections: dict
    overall_progress: float
    current_section: str
    current_section_progress: float
    total_words: int
    target_words: int
    paragraph_count: int
    content_density: dict
    milestones: List[dict]
    suggestion: str
    writing_duration: int


class EmotionCheckRequest(BaseModel):
    user_input: str
    help_round: int
    session_id: str


class EmotionResponse(BaseModel):
    level: str
    signals: List[dict]
    trigger_count: int
    encouragement: str
    should_cool_down: bool


class TrainingCardResponse(BaseModel):
    id: str
    skill_type: str
    difficulty: int
    duration: int
    title: str
    task: str
    constraints: List[str]
    hint: str
    example: Optional[str]


class TrainingEvaluateRequest(BaseModel):
    card_id: str
    user_text: str
    session_id: str


class TrainingEvaluateResponse(BaseModel):
    card_id: str
    skill_type: str
    highlights: List[str]
    suggestions: List[str]


class ReviewResponse(BaseModel):
    summary: dict
    stuck_analysis: dict
    timeline: List[dict]
    emotion_summary: dict
    ability_analysis: dict
    achievements: List[str]
    suggested_training: Optional[str]


class ParentSummaryResponse(BaseModel):
    topic: str
    duration: str
    word_count: int
    overview: str
    independence: str
    improvement: Optional[str]
    attention: Optional[str]


# === 模块一：卡壳类型智能识别 ===

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_content(req: AnalyzeRequest):
    """智能分析写作内容"""
    result = content_analyzer.quick_analyze(req.text)
    return AnalyzeResponse(**result)


# === 模块二：写作进度可视化 ===

@router.post("/progress/{session_id}/update")
async def update_progress(session_id: str, req: AnalyzeRequest):
    """更新写作进度"""
    if session_id not in progress_trackers:
        progress_trackers[session_id] = ProgressTracker()
        progress_trackers[session_id].start()
    
    tracker = progress_trackers[session_id]
    analysis = content_analyzer.analyze(req.text, req.cursor_pos)
    newly_triggered = tracker.update(analysis)
    
    return {
        "progress": tracker.get_progress_map(),
        "new_milestones": [
            {"name": m.name, "message": m.message}
            for m in newly_triggered
        ],
        "writing_duration": tracker.get_writing_duration(),
    }


@router.get("/progress/{session_id}", response_model=ProgressResponse)
async def get_progress(session_id: str):
    """获取当前写作进度"""
    if session_id not in progress_trackers:
        raise HTTPException(status_code=404, detail="Progress not found")
    
    tracker = progress_trackers[session_id]
    progress_map = tracker.get_progress_map()
    progress_map["writing_duration"] = tracker.get_writing_duration()
    
    return ProgressResponse(**progress_map)


# === 模块三：情绪感知与鼓励 ===

@router.post("/emotion/check", response_model=EmotionResponse)
async def check_emotion(req: EmotionCheckRequest):
    """检测用户情绪状态"""
    if req.session_id not in emotion_engines:
        emotion_engines[req.session_id] = EmotionEngine()
    
    engine = emotion_engines[req.session_id]
    analysis = content_analyzer.analyze(req.user_input)
    state = engine.analyze(req.user_input, req.help_round, analysis.emotion_signals)
    
    stuck_type = None
    encouragement = engine.get_encouragement(stuck_type, state.level)
    
    return EmotionResponse(
        level=state.level.value,
        signals=state.signals,
        trigger_count=state.trigger_count,
        encouragement=encouragement,
        should_cool_down=engine.should_cool_down(),
    )


@router.get("/emotion/{session_id}/report")
async def get_emotion_report(session_id: str):
    """获取情绪报告"""
    if session_id not in emotion_engines:
        return {"status": "no_data"}
    
    return emotion_engines[session_id].get_emotion_report()


# === 模块四：微写作训练舱 ===

@router.get("/training/daily", response_model=TrainingCardResponse)
async def get_daily_training(focus_skill: Optional[str] = None):
    """获取每日训练卡片"""
    card = training_deck.get_daily_training(focus_skill=focus_skill)
    return TrainingCardResponse(
        id=card.id,
        skill_type=card.skill_type,
        difficulty=card.difficulty,
        duration=card.duration,
        title=card.title,
        task=card.task,
        constraints=card.constraints,
        hint=card.hint,
        example=card.example,
    )


@router.get("/training/skills")
async def get_skills_status():
    """获取技能状态"""
    return training_deck.get_skill_status()


@router.post("/training/evaluate", response_model=TrainingEvaluateResponse)
async def evaluate_training(req: TrainingEvaluateRequest):
    """评估训练结果"""
    result = training_deck.evaluate_training(req.card_id, req.user_text)
    training_deck.record_completion(req.session_id, req.card_id, req.user_text)
    
    return TrainingEvaluateResponse(
        card_id=result["card_id"],
        skill_type=result["skill_type"],
        highlights=result["highlights"],
        suggestions=result["suggestions"],
    )


@router.get("/training/cards/{skill_type}")
async def get_training_cards(skill_type: str, difficulty: Optional[int] = None):
    """获取指定技能的训练卡片列表"""
    cards = training_deck.get_skill_training(skill_type, difficulty)
    return [
        TrainingCardResponse(
            id=c.id,
            skill_type=c.skill_type,
            difficulty=c.difficulty,
            duration=c.duration,
            title=c.title,
            task=c.task,
            constraints=c.constraints,
            hint=c.hint,
            example=c.example,
        )
        for c in cards
    ]


# === 模块五：写后过程复盘 ===

@router.post("/review/{session_id}/record-stuck")
async def record_stuck(
    session_id: str,
    stuck_type: str,
    help_rounds: int = 1,
    resolved: bool = True,
    resolution_time: int = 2,
):
    """记录卡壳事件"""
    if session_id not in session_writing_sessions:
        session_writing_sessions[session_id] = WritingSession(
            session_id=session_id,
            topic="",
            start_time=__import__('datetime').datetime.now(),
        )
    
    session = session_writing_sessions[session_id]
    
    record = StuckRecord(
        timestamp=__import__('datetime').datetime.now(),
        stuck_type=stuck_type,
        help_rounds=help_rounds,
        resolved=resolved,
        resolution_time=resolution_time,
    )
    session.stuck_records.append(record)
    
    return {
        "recorded": True,
        "total_stuck_count": len(session.stuck_records),
    }


@router.post("/review/{session_id}/complete")
async def complete_writing(
    session_id: str,
    total_words: int,
    total_duration: int,
):
    """完成写作，生成分复盘数据"""
    if session_id not in session_writing_sessions:
        raise HTTPException(status_code=404, detail="Writing session not found")
    
    session = session_writing_sessions[session_id]
    session.total_words = total_words
    session.total_duration = total_duration
    session.end_time = __import__('datetime').datetime.now()
    
    if session_id in progress_trackers:
        session.progress_snapshots = progress_trackers[session_id].get_progress_timeline()
    
    if session_id in emotion_engines:
        emotion_report = emotion_engines[session_id].get_emotion_report()
        session.emotion_events = [
            {"type": "emotion", "level": emotion_report.get("max_level_reached", "normal")}
        ]
    
    review_generator.add_session(session)
    
    return {
        "completed": True,
        "session_id": session_id,
        "total_words": total_words,
        "total_duration": total_duration,
    }


@router.get("/review/{session_id}", response_model=ReviewResponse)
async def get_review(session_id: str):
    """获取学生视角复盘报告"""
    review = review_generator.generate_review(session_id)
    if "error" in review:
        raise HTTPException(status_code=404, detail=review["error"])
    
    return ReviewResponse(
        summary=review["summary"],
        stuck_analysis=review["stuck_analysis"],
        timeline=review["timeline"],
        emotion_summary=review["emotion_summary"],
        ability_analysis=review["ability_analysis"],
        achievements=review["achievements"],
        suggested_training=review["suggested_training"],
    )


@router.get("/review/{session_id}/parent", response_model=ParentSummaryResponse)
async def get_parent_summary(session_id: str):
    """获取家长视角简报"""
    summary = review_generator.generate_parent_summary(session_id)
    if "error" in summary:
        raise HTTPException(status_code=404, detail=summary["error"])
    
    return ParentSummaryResponse(
        topic=summary["topic"],
        duration=summary["duration"],
        word_count=summary["word_count"],
        overview=summary["overview"],
        independence=summary["independence"],
        improvement=summary.get("improvement"),
        attention=summary.get("attention"),
    )


@router.get("/review/{user_id}/growth")
async def get_growth_report(user_id: str = "default", last_n: int = 5):
    """获取成长报告"""
    return review_generator.generate_growth_report(user_id, last_n)


# === 辅助端点 ===

@router.post("/session/{session_id}/sync")
async def sync_session_data(
    session_id: str,
    text: str,
    user_input: str,
    help_round: int = 0,
):
    """同步会话数据（一次调用更新所有模块）"""
    analysis = content_analyzer.quick_analyze(text)
    
    if session_id not in progress_trackers:
        progress_trackers[session_id] = ProgressTracker()
        progress_trackers[session_id].start()
    
    tracker = progress_trackers[session_id]
    analysis_result = content_analyzer.analyze(text)
    newly_triggered = tracker.update(analysis_result)
    
    if session_id not in emotion_engines:
        emotion_engines[session_id] = EmotionEngine()
    
    engine = emotion_engines[session_id]
    emotion_state = engine.analyze(user_input, help_round, analysis_result.emotion_signals)
    
    return {
        "analysis": analysis,
        "progress": tracker.get_progress_map(),
        "new_milestones": [
            {"name": m.name, "message": m.message}
            for m in newly_triggered
        ],
        "emotion": {
            "level": emotion_state.level.value,
            "encouragement": engine.get_encouragement(None, emotion_state.level),
            "should_cool_down": engine.should_cool_down(),
        },
        "writing_duration": tracker.get_writing_duration(),
    }
