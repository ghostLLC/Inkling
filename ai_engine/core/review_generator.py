"""
复盘报告生成器 - 写作过程复盘与成长追踪
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter


@dataclass
class StuckRecord:
    """卡壳记录"""
    timestamp: datetime
    stuck_type: str
    help_rounds: int
    resolved: bool
    resolution_time: int  # 分钟


@dataclass
class WritingSession:
    """写作会话记录"""
    session_id: str
    topic: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_words: int = 0
    total_duration: int = 0  # 分钟
    stuck_records: List[StuckRecord] = field(default_factory=list)
    emotion_events: List[Dict] = field(default_factory=list)
    progress_snapshots: List[Dict] = field(default_factory=list)
    training_completed: List[str] = field(default_factory=list)


class ReviewGenerator:
    """复盘报告生成器"""
    
    def __init__(self):
        self.sessions: List[WritingSession] = []
    
    def add_session(self, session: WritingSession):
        """添加会话记录"""
        self.sessions.append(session)
    
    def generate_review(self, session_id: str) -> Dict:
        """生成单次写作复盘报告"""
        session = self._find_session(session_id)
        if not session:
            return {"error": "会话不存在"}
        
        stuck_count = len(session.stuck_records)
        resolved_count = sum(1 for r in session.stuck_records if r.resolved)
        avg_help_rounds = (
            sum(r.help_rounds for r in session.stuck_records) / stuck_count
            if stuck_count > 0 else 0
        )
        
        ai_assisted_chars = sum(
            r.help_rounds * 50 for r in session.stuck_records
        ) if session.stuck_records else 0
        independent_ratio = max(
            0.5,
            1.0 - (ai_assisted_chars / max(session.total_words, 1))
        )
        
        stuck_types = [r.stuck_type for r in session.stuck_records]
        type_distribution = Counter(stuck_types)
        
        emotion_summary = self._summarize_emotion(session.emotion_events)
        timeline = self._generate_timeline(session)
        strongest, weakest = self._analyze_abilities(type_distribution)
        
        return {
            "session_id": session_id,
            "topic": session.topic,
            "summary": {
                "total_duration": session.total_duration,
                "total_words": session.total_words,
                "stuck_count": stuck_count,
                "resolved_count": resolved_count,
                "resolution_rate": round(resolved_count / stuck_count, 2) if stuck_count > 0 else 1.0,
                "avg_help_rounds": round(avg_help_rounds, 1),
                "independent_ratio": round(independent_ratio, 2),
            },
            "stuck_analysis": {
                "records": [
                    {
                        "time": self._format_time(r.timestamp),
                        "type": r.stuck_type,
                        "help_rounds": r.help_rounds,
                        "resolved": r.resolved,
                        "resolution_time": r.resolution_time,
                    }
                    for r in session.stuck_records
                ],
                "type_distribution": dict(type_distribution),
                "most_common": type_distribution.most_common(1)[0] if type_distribution else None,
            },
            "timeline": timeline,
            "emotion_summary": emotion_summary,
            "ability_analysis": {
                "strongest": strongest,
                "weakest": weakest,
                "next_challenge": self._suggest_next_challenge(weakest),
            },
            "achievements": self._generate_achievements(session),
            "suggested_training": self._suggest_training(type_distribution),
        }
    
    def generate_parent_summary(self, session_id: str) -> Dict:
        """生成家长视角简报"""
        session = self._find_session(session_id)
        if not session:
            return {"error": "会话不存在"}
        
        stuck_count = len(session.stuck_records)
        resolved_count = sum(1 for r in session.stuck_records if r.resolved)
        
        prev_session = self._get_previous_session(session_id)
        prev_stuck_count = len(prev_session.stuck_records) if prev_session else 0
        
        improvement = ""
        if stuck_count < prev_stuck_count:
            improvement = f"比上次少求助{prev_stuck_count - stuck_count}次"
        elif stuck_count == 0 and prev_stuck_count > 0:
            improvement = "本次全程独立完成"
        
        return {
            "topic": session.topic,
            "duration": f"{session.total_duration}分钟",
            "word_count": session.total_words,
            "overview": f"中途遇到困难{stuck_count}次，均在引导下继续完成" if stuck_count > 0 else "本次写作顺利完成",
            "independence": f"自主完成度：{self._estimate_independence(session):.0%}",
            "improvement": improvement if improvement else None,
            "attention": self._generate_parent_attention(session) if stuck_count > 0 else None,
        }
    
    def generate_growth_report(self, user_id: str = "default", last_n: int = 5) -> Dict:
        """生成成长报告"""
        recent_sessions = self.sessions[-last_n:] if len(self.sessions) >= last_n else self.sessions
        
        if not recent_sessions:
            return {"status": "no_data"}
        
        durations = [s.total_duration for s in recent_sessions]
        words = [s.total_words for s in recent_sessions]
        stuck_counts = [len(s.stuck_records) for s in recent_sessions]
        
        duration_trend = "stable"
        if len(durations) >= 2:
            if durations[-1] < durations[0] * 0.9:
                duration_trend = "decreasing"
            elif durations[-1] > durations[0] * 1.1:
                duration_trend = "increasing"
        
        stuck_trend = "stable"
        if len(stuck_counts) >= 2:
            if stuck_counts[-1] < stuck_counts[0]:
                stuck_trend = "decreasing"
            elif stuck_counts[-1] > stuck_counts[0]:
                stuck_trend = "increasing"
        
        all_stuck_types = []
        for s in recent_sessions:
            all_stuck_types.extend([r.stuck_type for r in s.stuck_records])
        
        type_distribution = Counter(all_stuck_types)
        
        return {
            "period": f"最近{len(recent_sessions)}次写作",
            "trends": {
                "duration": {
                    "values": durations,
                    "trend": duration_trend,
                    "message": self._trend_message(duration_trend, "写作时长"),
                },
                "stuck_count": {
                    "values": stuck_counts,
                    "trend": stuck_trend,
                    "message": self._trend_message(stuck_trend, "卡壳次数"),
                },
                "word_count": {
                    "values": words,
                    "trend": "stable",
                    "message": f"平均{sum(words)//len(words)}字/次",
                },
            },
            "common_stuck_types": dict(type_distribution.most_common(3)),
            "overall_assessment": self._overall_assessment(recent_sessions),
        }
    
    def _find_session(self, session_id: str) -> Optional[WritingSession]:
        return next((s for s in self.sessions if s.session_id == session_id), None)
    
    def _get_previous_session(self, session_id: str) -> Optional[WritingSession]:
        idx = next((i for i, s in enumerate(self.sessions) if s.session_id == session_id), -1)
        if idx > 0:
            return self.sessions[idx - 1]
        return None
    
    def _format_time(self, dt: datetime) -> str:
        return dt.strftime("%H:%M")
    
    def _summarize_emotion(self, emotion_events: List[Dict]) -> Dict:
        if not emotion_events:
            return {"status": "stable", "events": []}
        
        severe_events = [e for e in emotion_events if e.get("severity") in ["medium", "heavy"]]
        
        return {
            "status": "needs_attention" if severe_events else "stable",
            "total_events": len(emotion_events),
            "severe_events": len(severe_events),
            "events": [
                {
                    "type": e.get("type"),
                    "severity": e.get("severity"),
                    "indicator": e.get("indicator"),
                }
                for e in emotion_events[:3]
            ],
        }
    
    def _generate_timeline(self, session: WritingSession) -> List[Dict]:
        timeline = []
        timeline.append({"time": "开始", "type": "start", "content": "开始写作"})
        
        for record in session.stuck_records:
            timeline.append({
                "time": self._format_time(record.timestamp),
                "type": "stuck",
                "content": f"卡壳：{record.stuck_type}（求助{record.help_rounds}轮）",
                "resolved": record.resolved,
            })
        
        if session.end_time:
            timeline.append({
                "time": self._format_time(session.end_time),
                "type": "end",
                "content": f"完成写作（{session.total_words}字）",
            })
        
        return timeline
    
    def _analyze_abilities(self, type_distribution: Counter) -> Tuple[str, str]:
        if not type_distribution:
            return "整体写作", "细节描写"
        
        most_common = type_distribution.most_common()
        
        stuck_to_ability = {
            "情节推进卡": "情节设计",
            "细节展开卡": "细节描写",
            "过渡衔接卡": "过渡衔接",
            "情感表达卡": "情感表达",
            "段落结构卡": "结构安排",
            "心理描写卡": "心理描写",
        }
        
        weakest = stuck_to_ability.get(most_common[0][0], "细节描写")
        
        if len(most_common) >= 2:
            strongest = stuck_to_ability.get(most_common[-1][0], "叙事推进")
        else:
            strongest = "叙事推进"
        
        return strongest, weakest
    
    def _suggest_next_challenge(self, weakest: str) -> str:
        challenges = {
            "情节设计": "下次试试在写前用1分钟列3个情节节点",
            "细节描写": "下次挑战：加入一段感官描写",
            "过渡衔接": "下次挑战：用一句话完成场景切换",
            "情感表达": "下次挑战：结尾用'我明白了'开头",
            "结构安排": "下次挑战：先写中间再写开头",
            "心理描写": "下次挑战：不写'我想'，直接写内心独白",
        }
        return challenges.get(weakest, "继续保持")
    
    def _generate_achievements(self, session: WritingSession) -> List[str]:
        achievements = []
        
        if session.total_words >= 500:
            achievements.append(f"完成{session.total_words}字写作")
        
        stuck_count = len(session.stuck_records)
        if stuck_count > 0:
            resolved = sum(1 for r in session.stuck_records if r.resolved)
            if resolved == stuck_count:
                achievements.append(f"克服{stuck_count}次卡壳")
        else:
            achievements.append("全程独立完成")
        
        if session.total_duration >= 30:
            achievements.append(f"专注写作{session.total_duration}分钟")
        
        prev = self._get_previous_session(session.session_id)
        if prev:
            if stuck_count < len(prev.stuck_records):
                achievements.append(f"比上次少求助{len(prev.stuck_records) - stuck_count}次")
        
        return achievements
    
    def _suggest_training(self, type_distribution: Counter) -> Optional[str]:
        if not type_distribution:
            return None
        
        most_common = type_distribution.most_common(1)[0][0]
        
        stuck_to_training = {
            "情节推进卡": "动作链描写训练",
            "细节展开卡": "感官聚焦训练",
            "过渡衔接卡": "时空切换训练",
            "情感表达卡": "一句话点题训练",
            "心理描写卡": "内心独白训练",
        }
        
        return stuck_to_training.get(most_common)
    
    def _estimate_independence(self, session: WritingSession) -> float:
        if session.total_words == 0:
            return 1.0
        
        assisted = sum(r.help_rounds * 30 for r in session.stuck_records)
        ratio = 1.0 - (assisted / session.total_words)
        return max(0.5, min(1.0, ratio))
    
    def _generate_parent_attention(self, session: WritingSession) -> str:
        type_distribution = Counter(r.stuck_type for r in session.stuck_records)
        most_common = type_distribution.most_common(1)[0][0] if type_distribution else None
        
        attention_map = {
            "情节推进卡": "可以多聊聊生活中的故事，积累情节素材",
            "细节展开卡": "日常可以玩'描述一个物品'的观察游戏",
            "过渡衔接卡": "阅读时留意作者怎么切换场景",
            "情感表达卡": "多和孩子讨论'这件事让你学到了什么'",
            "心理描写卡": "鼓励孩子说出内心的想法，不评价对错",
        }
        
        return attention_map.get(most_common, "继续鼓励孩子多写多练")
    
    def _trend_message(self, trend: str, metric: str) -> str:
        messages = {
            "increasing": f"{metric}有所上升",
            "decreasing": f"{metric}下降，有进步",
            "stable": f"{metric}保持稳定",
        }
        return messages.get(trend, f"{metric}无明显变化")
    
    def _overall_assessment(self, sessions: List[WritingSession]) -> str:
        total_stuck = sum(len(s.stuck_records) for s in sessions)
        avg_stuck = total_stuck / len(sessions) if sessions else 0
        
        if avg_stuck == 0:
            return "写作状态非常好，全程独立完成"
        elif avg_stuck <= 2:
            return "写作状态良好，偶尔需要帮助"
        elif avg_stuck <= 4:
            return "写作过程有挑战，但都能完成"
        else:
            return "写作过程较困难，建议多进行专项训练"
