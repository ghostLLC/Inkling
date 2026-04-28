"""
情绪引擎 - 挫败检测与分层鼓励
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class EmotionLevel(Enum):
    """挫败等级"""
    NORMAL = "normal"      # 正常
    LIGHT = "light"        # 轻度挫败
    MEDIUM = "medium"      # 中度挫败
    HEAVY = "heavy"        # 重度挫败


@dataclass
class EmotionState:
    """情绪状态"""
    level: EmotionLevel
    signals: List[Dict]
    trigger_count: int
    last_trigger: Optional[str] = None
    consecutive_help_rejected: int = 0  # 连续"还是不会"次数


class EmotionEngine:
    """情绪感知与鼓励引擎"""
    
    # 鼓励话术库
    ENCOURAGEMENT_LIBRARY = {
        EmotionLevel.NORMAL: [
            "先写一句，不用完美。",
            "试试从你印象最深的那个画面开始。",
            "把脑子里的画面直接描述出来，不用管顺序。",
            "你已经把背景写清楚了，人物该出场了。",
            "往下走，写出来再说。",
        ],
        EmotionLevel.LIGHT: [
            "卡住是正常的，深呼吸一下。",
            "先写3句话试试，写完再看。",
            "不用一次想完整段，一小步一小步走。",
            "把'然后'后面的事直接写出来，不用修饰。",
        ],
        EmotionLevel.MEDIUM: [
            "卡住了很正常，我看看你已经写的...这段其实有感觉的。",
            "不用一次想完整段，先写3句话试试？",
            "如果你跟朋友讲这个故事，你会怎么说？",
            "你已经完成一大半了，剩下的只是把它说完。",
            "写作不是一次性写对的，是先写出来再改。",
        ],
        EmotionLevel.HEAVY: [
            "先停一下。写作卡住不代表你不行，只是需要换个入口。",
            "我们来做一道选择题：接下来你想让故事A.继续发展 B.换个场景 C.加入对话",
            "不用写了，先回答我：主角现在最想做什么？",
            "今天的目标是写完，不是写好。先完成，再完美。",
            "你已经走到这里了，这比很多人强了。",
        ],
    }
    
    # 语气标记词
    TONE_MARKERS = {
        EmotionLevel.NORMAL: [],
        EmotionLevel.LIGHT: ["试试", "看看", "先写"],
        EmotionLevel.MEDIUM: ["我们", "不用急", "慢慢来"],
        EmotionLevel.HEAVY: ["先停一下", "没事", "没关系", "你已经"],
    }
    
    # 负面信号词（触发挫败检测）
    NEGATIVE_SIGNALS = {
        "heavy": ["不想写了", "太难了", "放弃", "算了", "不会写", "写不下去"],
        "medium": ["还是不会", "还是不懂", "没懂", "不太明白", "还是有点卡"],
        "light": ["不会", "不知道怎么", "有点难", "卡住了", "迷茫"],
    }
    
    def __init__(self):
        self.help_round_count: int = 0
        self.consecutive_rejected: int = 0
        self.emotion_history: List[EmotionState] = []
        self.current_level: EmotionLevel = EmotionLevel.NORMAL
        self.cool_down_active: bool = False
    
    def analyze(self, user_input: str, help_round: int, emotion_signals: List[Dict]) -> EmotionState:
        """
        分析用户情绪状态
        
        Args:
            user_input: 用户最新输入
            help_round: 当前求助轮数
            emotion_signals: 来自内容分析器的情绪信号
        """
        signals = []
        
        # 1. 检测文本中的负面信号
        text_signals = self._detect_text_signals(user_input)
        signals.extend(text_signals)
        
        # 2. 检测求助轮数
        if help_round >= 3:
            signals.append({
                "type": "help_round_exceeded",
                "severity": "medium" if help_round < 5 else "heavy",
                "indicator": f"已求助{help_round}轮"
            })
        
        # 3. 整合内容分析器的信号
        for signal in emotion_signals:
            signals.append(signal)
        
        # 4. 检测连续拒绝
        if self._is_help_rejected(user_input):
            self.consecutive_rejected += 1
            if self.consecutive_rejected >= 2:
                signals.append({
                    "type": "consecutive_rejected",
                    "severity": "medium" if self.consecutive_rejected < 4 else "heavy",
                    "indicator": f"连续{self.consecutive_rejected}次表示未解决"
                })
        else:
            self.consecutive_rejected = 0
        
        # 5. 判断挫败等级
        level = self._calculate_level(signals, help_round)
        
        # 6. 更新历史
        state = EmotionState(
            level=level,
            signals=signals,
            trigger_count=len(signals),
            consecutive_help_rejected=self.consecutive_rejected,
        )
        self.emotion_history.append(state)
        self.current_level = level
        
        return state
    
    def _detect_text_signals(self, text: str) -> List[Dict]:
        """检测文本中的情绪信号"""
        signals = []
        
        for severity, words in self.NEGATIVE_SIGNALS.items():
            for word in words:
                if word in text:
                    signals.append({
                        "type": "negative_word",
                        "severity": severity,
                        "indicator": f"检测到：{word}"
                    })
        
        return signals
    
    def _is_help_rejected(self, text: str) -> bool:
        """判断用户是否表示帮助未解决"""
        reject_patterns = [
            "还是不会", "还是不懂", "没懂", "不太明白", "还是有点卡",
            "还是不知道", "还是写不出来", "还是卡住", "没用", "没帮助"
        ]
        return any(p in text for p in reject_patterns)
    
    def _calculate_level(self, signals: List[Dict], help_round: int) -> EmotionLevel:
        """计算挫败等级"""
        if not signals:
            return EmotionLevel.NORMAL
        
        # 统计各severity数量
        severity_counts = {"light": 0, "medium": 0, "heavy": 0}
        for signal in signals:
            sev = signal.get("severity", "light")
            if sev in severity_counts:
                severity_counts[sev] += 1
        
        # 判断逻辑
        if severity_counts["heavy"] >= 1 or help_round >= 5:
            return EmotionLevel.HEAVY
        elif severity_counts["medium"] >= 2 or (severity_counts["medium"] >= 1 and help_round >= 3):
            return EmotionLevel.MEDIUM
        elif severity_counts["light"] >= 2 or help_round >= 2:
            return EmotionLevel.LIGHT
        
        return EmotionLevel.NORMAL
    
    def get_encouragement(self, stuck_type: Optional[str] = None, level: Optional[EmotionLevel] = None) -> str:
        """
        获取鼓励话术
        
        Args:
            stuck_type: 卡壳类型（用于个性化鼓励）
            level: 挫败等级（默认使用当前检测到的等级）
        """
        if level is None:
            level = self.current_level
        
        # 获取基础话术
        base_encouragements = self.ENCOURAGEMENT_LIBRARY.get(level, [])
        
        if not base_encouragements:
            return ""
        
        # 根据卡壳类型选择最合适的话术（简单匹配）
        import random
        selected = random.choice(base_encouragements)
        
        # 如果是重度挫败，添加具体行动指令
        if level == EmotionLevel.HEAVY:
            if stuck_type and "情节" in stuck_type:
                selected += "\n\n现在只做一件事：写下主角接下来做的第一个动作。"
            elif stuck_type and "描写" in stuck_type:
                selected += "\n\n现在只做一件事：描述你眼前看到的3个颜色。"
            elif stuck_type and "结尾" in stuck_type:
                selected += "\n\n现在只做一件事：用一句话说出这件事让你明白了什么。"
        
        return selected
    
    def get_tone_markers(self, level: Optional[EmotionLevel] = None) -> List[str]:
        """获取当前语气标记词"""
        if level is None:
            level = self.current_level
        return self.TONE_MARKERS.get(level, [])
    
    def should_cool_down(self) -> bool:
        """是否应该进入冷却模式"""
        return self.current_level >= EmotionLevel.MEDIUM and self.consecutive_rejected >= 2
    
    def get_emotion_report(self) -> Dict:
        """获取情绪报告（用于复盘）"""
        if not self.emotion_history:
            return {"status": "normal", "events": []}
        
        # 统计各等级出现次数
        level_counts = {level: 0 for level in EmotionLevel}
        for state in self.emotion_history:
            level_counts[state.level] += 1
        
        # 找出最严重的事件
        max_level = max(self.emotion_history, key=lambda x: list(EmotionLevel).index(x.level))
        
        return {
            "current_level": self.current_level.value,
            "max_level_reached": max_level.level.value,
            "level_distribution": {k.value: v for k, v in level_counts.items()},
            "total_events": len(self.emotion_history),
            "consecutive_rejected_max": max(
                (s.consecutive_help_rejected for s in self.emotion_history),
                default=0
            ),
            "needs_attention": self.current_level >= EmotionLevel.MEDIUM,
        }
    
    def reset(self):
        """重置状态"""
        self.help_round_count = 0
        self.consecutive_rejected = 0
        self.emotion_history = []
        self.current_level = EmotionLevel.NORMAL
        self.cool_down_active = False
