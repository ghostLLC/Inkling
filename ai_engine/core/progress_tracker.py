"""进度追踪器 - 写作进度可视化与里程碑管理
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProgressSnapshot:
    """进度快照"""

    timestamp: datetime
    word_count: int
    paragraph_count: int
    section: str  # 开头/中段/结尾
    section_progress: float
    content_density: dict[str, float]


@dataclass
class Milestone:
    """里程碑"""

    name: str
    description: str
    threshold: float  # 触发阈值（进度百分比）
    triggered: bool = False
    triggered_at: datetime | None = None
    message: str = ""


class ProgressTracker:
    """写作进度追踪器"""

    # 里程碑定义
    MILESTONES = [
        Milestone(
            name="开头完成",
            description="开头段落已建立",
            threshold=0.2,
            message="开头搭好了，继续推进故事吧 🏗️"
        ),
        Milestone(
            name="进入中段",
            description="进入故事主体",
            threshold=0.3,
            message="故事要开始了，这是最重要的部分 📖"
        ),
        Milestone(
            name="中段过半",
            description="中段已完成过半",
            threshold=0.5,
            message="已经过半了，注意控制节奏 🔄"
        ),
        Milestone(
            name="接近结尾",
            description="准备进入结尾",
            threshold=0.8,
            message="准备 landing，想想怎么收束 🏆"
        ),
        Milestone(
            name="即将完成",
            description="即将完成全文",
            threshold=0.95,
            message="最后一段了，把点题的话说清楚 ✨"
        ),
    ]

    def __init__(self):
        self.snapshots: list[ProgressSnapshot] = []
        self.milestones: list[Milestone] = [self._clone_milestone(m) for m in self.MILESTONES]
        self.total_target_words: int = 650  # 目标字数（记叙文标准）
        self.start_time: datetime | None = None
        self.last_update: datetime | None = None

    def _clone_milestone(self, m: Milestone) -> Milestone:
        """克隆里程碑"""
        return Milestone(
            name=m.name,
            description=m.description,
            threshold=m.threshold,
            triggered=False,
            triggered_at=None,
            message=m.message
        )

    def start(self):
        """开始追踪"""
        self.start_time = datetime.now()
        self.last_update = datetime.now()

    def update(self, analysis_result: "AnalysisResult") -> list[Milestone]:
        """更新进度，返回新触发的里程碑
        """
        if self.start_time is None:
            self.start()

        # 创建快照
        snapshot = ProgressSnapshot(
            timestamp=datetime.now(),
            word_count=analysis_result.word_count,
            paragraph_count=analysis_result.paragraph_count,
            section=analysis_result.section,
            section_progress=analysis_result.section_progress,
            content_density=analysis_result.content_density.copy(),
        )
        self.snapshots.append(snapshot)
        self.last_update = datetime.now()

        # 计算整体进度（基于字数和段落）
        word_progress = min(analysis_result.word_count / self.total_target_words, 1.0)
        section_weight = {
            "开头": 0.2,
            "中段": 0.6,
            "结尾": 0.2,
        }

        current_section_weight = section_weight.get(analysis_result.section, 0.2)
        overall_progress = 0.0

        # 累加已完成的部分
        if analysis_result.section == "开头":
            overall_progress = analysis_result.section_progress * current_section_weight
        elif analysis_result.section == "中段":
            overall_progress = 0.2 + analysis_result.section_progress * current_section_weight
        else:  # 结尾
            overall_progress = 0.8 + analysis_result.section_progress * current_section_weight

        overall_progress = min(overall_progress, 1.0)

        # 检查里程碑
        newly_triggered = []
        for milestone in self.milestones:
            if not milestone.triggered and overall_progress >= milestone.threshold:
                milestone.triggered = True
                milestone.triggered_at = datetime.now()
                newly_triggered.append(milestone)

        return newly_triggered

    def get_progress_map(self) -> dict:
        """获取进度地图数据（用于前端可视化）
        """
        if not self.snapshots:
            return self._empty_progress_map()

        latest = self.snapshots[-1]

        # 计算各段进度
        intro_progress = 1.0 if latest.section != "开头" else latest.section_progress
        body_progress = (
            latest.section_progress if latest.section == "中段"
            else (1.0 if latest.section == "结尾" else 0.0)
        )
        ending_progress = latest.section_progress if latest.section == "结尾" else 0.0

        # 整体进度
        word_progress = min(latest.word_count / self.total_target_words, 1.0)

        return {
            "sections": {
                "introduction": {
                    "name": "开头",
                    "progress": round(intro_progress, 2),
                    "status": "completed" if intro_progress >= 1.0 else "active" if latest.section == "开头" else "pending",
                    "word_count": self._estimate_section_words("开头", latest),
                },
                "body": {
                    "name": "中段",
                    "progress": round(body_progress, 2),
                    "status": "completed" if latest.section == "结尾" else "active" if latest.section == "中段" else "pending",
                    "word_count": self._estimate_section_words("中段", latest),
                },
                "ending": {
                    "name": "结尾",
                    "progress": round(ending_progress, 2),
                    "status": "active" if latest.section == "结尾" else "pending",
                    "word_count": self._estimate_section_words("结尾", latest),
                },
            },
            "overall_progress": round(word_progress, 2),
            "current_section": latest.section,
            "current_section_progress": round(latest.section_progress, 2),
            "total_words": latest.word_count,
            "target_words": self.total_target_words,
            "paragraph_count": latest.paragraph_count,
            "content_density": {k: round(v, 2) for k, v in latest.content_density.items()},
            "milestones": [
                {
                    "name": m.name,
                    "triggered": m.triggered,
                    "message": m.message if m.triggered else None,
                    "threshold": m.threshold,
                }
                for m in self.milestones
            ],
            "suggestion": self._get_current_suggestion(latest),
        }

    def _empty_progress_map(self) -> dict:
        """空进度地图"""
        return {
            "sections": {
                "introduction": {"name": "开头", "progress": 0, "status": "pending", "word_count": 0},
                "body": {"name": "中段", "progress": 0, "status": "pending", "word_count": 0},
                "ending": {"name": "结尾", "progress": 0, "status": "pending", "word_count": 0},
            },
            "overall_progress": 0,
            "current_section": "开头",
            "current_section_progress": 0,
            "total_words": 0,
            "target_words": self.total_target_words,
            "paragraph_count": 0,
            "content_density": {"narrative": 0, "description": 0, "dialogue": 0, "psychology": 0},
            "milestones": [
                {"name": m.name, "triggered": False, "message": None, "threshold": m.threshold}
                for m in self.milestones
            ],
            "suggestion": "开始写作吧！先写出第一段。",
        }

    def _estimate_section_words(self, section: str, latest: ProgressSnapshot) -> int:
        """估算各段字数"""
        if section == "开头":
            if latest.section == "开头":
                return latest.word_count
            return min(latest.word_count, 150)
        elif section == "中段":
            if latest.section == "开头":
                return 0
            elif latest.section == "中段":
                return latest.word_count - 150
            return max(latest.word_count - 500, 0)
        else:  # 结尾
            if latest.section != "结尾":
                return 0
            return latest.word_count - 500

    def _get_current_suggestion(self, latest: ProgressSnapshot) -> str:
        """基于当前进度给出建议"""
        section = latest.section
        progress = latest.section_progress
        density = latest.content_density

        if section == "开头":
            if progress < 0.3:
                return "先交代背景，尽快引入主要人物或事件"
            elif progress < 0.7:
                return "开头即将完成，准备进入故事主体"
            else:
                return "开头差不多了，该进入主要事件了"

        elif section == "中段":
            if progress < 0.3:
                return "中段刚开始，先推进事件发展"
            elif progress < 0.6:
                if density["description"] < 0.3:
                    return "事件在推进，试试加入细节描写让画面更生动"
                return "节奏不错，继续保持"
            else:
                return "中段快结束了，想想怎么自然过渡到结尾"

        else:  # 结尾
            if progress < 0.3:
                return "结尾刚开始，先回扣题目"
            elif progress < 0.7:
                return "把感悟或成长说清楚，不要绕"
            else:
                return "最后润色一下，确保点题清晰"

    def get_writing_duration(self) -> int:
        """获取写作时长（分钟）"""
        if self.start_time is None:
            return 0
        delta = datetime.now() - self.start_time
        return int(delta.total_seconds() / 60)

    def get_progress_timeline(self) -> list[dict]:
        """获取进度时间轴数据（用于复盘）"""
        timeline = []
        for snapshot in self.snapshots:
            timeline.append({
                "timestamp": snapshot.timestamp.isoformat(),
                "word_count": snapshot.word_count,
                "section": snapshot.section,
                "section_progress": round(snapshot.section_progress, 2),
            })
        return timeline

    def to_dict(self) -> dict:
        """序列化"""
        return {
            "snapshots_count": len(self.snapshots),
            "milestones": [
                {
                    "name": m.name,
                    "triggered": m.triggered,
                    "triggered_at": m.triggered_at.isoformat() if m.triggered_at else None,
                }
                for m in self.milestones
            ],
            "writing_duration": self.get_writing_duration(),
            "current_progress": self.get_progress_map(),
        }
