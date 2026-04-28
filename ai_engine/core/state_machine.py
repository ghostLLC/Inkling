"""状态机模块 - 管理每个写作会话的状态流转
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any


class TaskMode(Enum):
    """任务模式"""

    TOPIC_ANALYSIS = auto()      # 审题立意阶段
    STUCK_RESCUE = auto()        # 卡壳救援阶段
    ENDING_GUIDE = auto()        # 结尾收束阶段
    COMPLETE = auto()            # 写作完成


class GuideLevel(Enum):
    """引导层级"""

    L1_DIRECTION = 1      # 方向引导
    L2_STRUCTURE = 2      # 结构提示
    L3_KEYWORDS = 3       # 关键词启发
    L4_EXAMPLES = 4       # 示例句（最高层）


class StuckType(Enum):
    """卡壳类型"""

    TYPE_1_PLOT = "情节推进卡"          # 不知道故事接下来怎么发展
    TYPE_2_DETAIL = "细节展开卡"        # 不会写具体画面
    TYPE_3_TRANSITION = "过渡衔接卡"    # 两段之间接不上
    TYPE_4_EMOTION = "情感表达卡"       # 不会表达感受/主题
    TYPE_5_PARAGRAPH = "段落结构卡"      # 不知道这段该承担什么功能
    TYPE_6_PSYCHOLOGY = "心理描写卡"     # 不会写内心活动


@dataclass
class SessionState:
    """会话状态"""

    session_id: str
    task_mode: TaskMode = TaskMode.TOPIC_ANALYSIS
    topic: str = ""                          # 作文题目
    written_content: str = ""               # 已写正文内容
    stuck_count: int = 0                      # 当前卡壳点累计求助次数
    total_stuck_count: int = 0                # 本次写作累计卡壳次数
    current_level: GuideLevel = GuideLevel.L1_DIRECTION
    current_stuck_type: StuckType | None = None
    selected_ending_strategy: str | None = None
    conversation_history: list = field(default_factory=list)  # 对话历史
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    topic_analysis_complete: bool = False     # 审题是否完成
    has_introduction: bool = False             # 是否有开头
    has_body: bool = False                      # 是否有正文
    has_ending: bool = False                    # 是否有结尾

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "session_id": self.session_id,
            "task_mode": self.task_mode.name,
            "topic": self.topic,
            "stuck_count": self.stuck_count,
            "total_stuck_count": self.total_stuck_count,
            "current_level": self.current_level.value,
            "current_stuck_type": self.current_stuck_type.value if self.current_stuck_type else None,
            "selected_ending_strategy": self.selected_ending_strategy,
            "topic_analysis_complete": self.topic_analysis_complete,
            "has_introduction": self.has_introduction,
            "has_body": self.has_body,
            "has_ending": self.has_ending,
        }

    def advance_level(self) -> GuideLevel:
        """推进到下一引导层级，最高到L4"""
        if self.current_level == GuideLevel.L1_DIRECTION:
            self.current_level = GuideLevel.L2_STRUCTURE
        elif self.current_level == GuideLevel.L2_STRUCTURE:
            self.current_level = GuideLevel.L3_KEYWORDS
        elif self.current_level == GuideLevel.L3_KEYWORDS:
            self.current_level = GuideLevel.L4_EXAMPLES
        self.stuck_count += 1
        return self.current_level

    def reset_level(self):
        """切换新卡壳点时重置层级"""
        self.current_level = GuideLevel.L1_DIRECTION
        self.stuck_count = 0
        self.current_stuck_type = None

    def should_cool_down(self) -> bool:
        """是否需要冷却提醒"""
        return self.stuck_count >= 3

    def complete_topic_analysis(self):
        """完成审题，切换到卡壳救援模式"""
        self.topic_analysis_complete = True
        self.task_mode = TaskMode.STUCK_RESCUE
        self.reset_level()

    def start_ending_guide(self):
        """进入结尾收束模式"""
        self.task_mode = TaskMode.ENDING_GUIDE
        self.reset_level()

    def complete_writing(self):
        """完成写作"""
        self.task_mode = TaskMode.COMPLETE

    def add_message(self, role: str, content: str):
        """添加对话记录"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.last_active = datetime.now()

    def update_written_content(self, content: str):
        """更新已写内容"""
        self.written_content = content
        # 判断写作进度
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        total_chars = len(content.replace('\n', '').replace(' ', ''))
        if len(paragraphs) >= 1 or total_chars > 30:
            self.has_introduction = True
        if len(paragraphs) >= 2 or total_chars > 80:
            self.has_body = True
        if len(paragraphs) >= 3 or total_chars > 150:
            self.has_ending = True
        if len(paragraphs) >= 2:
            self.has_body = True
        if len(paragraphs) >= 3:
            self.has_ending = True


class StateMachine:
    """状态机管理器"""

    def __init__(self):
        self.sessions: dict[str, SessionState] = {}

    def create_session(self, session_id: str) -> SessionState:
        """创建新会话"""
        session = SessionState(session_id=session_id)
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> SessionState | None:
        """获取会话状态"""
        return self.sessions.get(session_id)

    def delete_session(self, session_id: str):
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]

    def get_active_sessions(self) -> list:
        """获取所有活跃会话"""
        return list(self.sessions.keys())

    def transition_mode(self, session_id: str, new_mode: TaskMode) -> bool:
        """手动切换模式（用于测试或特殊场景）"""
        session = self.get_session(session_id)
        if not session:
            return False
        session.task_mode = new_mode
        if new_mode == TaskMode.STUCK_RESCUE:
            session.reset_level()
        elif new_mode == TaskMode.ENDING_GUIDE:
            session.reset_level()
        return True
