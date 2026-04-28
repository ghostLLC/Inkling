"""微写作训练舱 - 写作技能组件化训练（简化版）
"""
import random
from dataclasses import dataclass
from enum import Enum


class SkillLevel(Enum):
    """技能水平"""

    LOCKED = "locked"
    BEGINNER = "beginner"
    DEVELOPING = "developing"
    PROFICIENT = "proficient"


@dataclass
class TrainingCard:
    """训练卡片"""

    id: str
    skill_type: str
    difficulty: int
    duration: int
    title: str
    task: str
    constraints: list[str]
    hint: str
    example: str | None = None


class TrainingDeck:
    """微写作训练舱"""

    TRAINING_LIBRARY = [
        TrainingCard(
            id="ACTION_CHAIN_001",
            skill_type="动作描写",
            difficulty=1,
            duration=3,
            title="动作链：紧张到放松",
            task="描写一个人从紧张到放松的动作变化过程",
            constraints=["至少3个连续动作", "不出现'紧张''放松'等直接形容词", "通过动作让读者感受到情绪变化"],
            hint="从肩膀、手指、呼吸这些细节入手",
            example="他的手指先是在膝盖上快速敲打，然后慢慢停住，最后垂在身侧，随着呼气轻轻张开。",
        ),
        TrainingCard(
            id="SENSORY_001",
            skill_type="感官聚焦",
            difficulty=1,
            duration=3,
            title="听觉聚焦：3种声音",
            task="描述你当前能听到的3种声音，让读者'听'到画面",
            constraints=["3种不同声音", "不出现'听到'二字", "每种声音不超过15字"],
            hint="用拟声词或直接描述声音质感",
            example="键盘敲击的嗒嗒声；窗外偶尔传来的汽车引擎低鸣；空调运转时细微的嗡鸣。",
        ),
        TrainingCard(
            id="PSYCHOLOGY_001",
            skill_type="心理描写",
            difficulty=1,
            duration=3,
            title="内心独白：不说'我想'",
            task="写一段主角独处时的内心活动",
            constraints=["不出现'我想''我觉得'", "至少3个内心活动", "有矛盾或转折"],
            hint="用疑问句、感叹句、假设句来暗示心理",
            example="要是当时说了那句话呢？现在也不会这样。可是说了又能改变什么？",
        ),
        TrainingCard(
            id="TRANSITION_001",
            skill_type="过渡衔接",
            difficulty=1,
            duration=3,
            title="时空切换：一句话过渡",
            task="用一句话完成从教室到操场的场景切换",
            constraints=["一句话", "不出现'然后''接着'", "有时间或空间线索"],
            hint="用光线、声音、温度等感官变化暗示场景切换",
            example="走廊尽头传来下课铃声时，我已经站在操场中央，阳光比教室里刺眼了十倍。",
        ),
        TrainingCard(
            id="ENDING_001",
            skill_type="结尾收束",
            difficulty=1,
            duration=3,
            title="一句话点题",
            task="给一个开头写一个不超过50字的结尾，必须回扣题目",
            constraints=["不超过50字", "必须提到题目关键词", "有感悟或成长"],
            hint="先说出事件结果，再说出这件事让你明白的道理",
            example="原来长大不是身高变了，而是终于懂得，那句话里藏着我一直没听出来的关心。",
        ),
        TrainingCard(
            id="FREE_001",
            skill_type="自由练笔",
            difficulty=1,
            duration=5,
            title="随机触发器：钥匙",
            task="以'一把钥匙掉在地上'为触发点，写100字以内的片段",
            constraints=["100字以内", "包含声音描写", "不出现'钥匙'二字"],
            hint="用掉落的声音、滚动轨迹、捡起的动作来暗示",
            example="金属撞击地面的脆响，滚了几圈，停在我脚边。我弯腰捡起，冰凉的触感从指尖传来。",
        ),
    ]

    def __init__(self):
        self.user_progress: dict[str, dict] = {}
        self.skill_levels: dict[str, SkillLevel] = {}
        self._initialize_skills()

    def _initialize_skills(self):
        """初始化技能状态"""
        all_skills = set(card.skill_type for card in self.TRAINING_LIBRARY)
        for skill in all_skills:
            self.skill_levels[skill] = SkillLevel.BEGINNER

    def get_daily_training(self, user_id: str = "default", focus_skill: str | None = None):
        """获取每日训练卡片"""
        available_cards = self.TRAINING_LIBRARY

        if focus_skill:
            skill_cards = [c for c in available_cards if c.skill_type == focus_skill]
            if skill_cards:
                return random.choice(skill_cards)

        return random.choice(available_cards)

    def get_skill_training(self, skill_type: str, difficulty: int | None = None):
        """获取指定技能的训练卡片"""
        cards = [c for c in self.TRAINING_LIBRARY if c.skill_type == skill_type]
        if difficulty is not None:
            cards = [c for c in cards if c.difficulty == difficulty]
        return cards

    def evaluate_training(self, card_id: str, user_text: str) -> dict:
        """轻量评估训练结果"""
        card = next((c for c in self.TRAINING_LIBRARY if c.id == card_id), None)
        if not card:
            return {"error": "卡片不存在"}

        highlights = []
        suggestions = []

        # 简单评估逻辑
        if card.skill_type == "动作描写":
            action_words = ["了", "着", "过", "去", "来", "走", "跑", "拿", "放"]
            action_count = sum(1 for w in action_words if w in user_text)
            if action_count >= 3:
                highlights.append("动作链条很清晰")
            else:
                suggestions.append("试试加入更多连续动作")

        if len(user_text) <= 100 and card.id != "FREE_001":
            highlights.append("字数控制很好")
        elif len(user_text) > 100:
            suggestions.append("可以再精简一些")

        if not highlights:
            highlights.append("完成了训练，这本身就是进步")

        return {
            "card_id": card_id,
            "skill_type": card.skill_type,
            "highlights": highlights[:2],
            "suggestions": suggestions[:1],
        }

    def record_completion(self, user_id: str, card_id: str, user_text: str):
        """记录训练完成"""
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {
                "completed_cards": [],
                "skill_counts": {},
            }

        progress = self.user_progress[user_id]
        card = next((c for c in self.TRAINING_LIBRARY if c.id == card_id), None)
        if card:
            progress["completed_cards"].append({
                "card_id": card_id,
                "skill_type": card.skill_type,
            })
            skill = card.skill_type
            progress["skill_counts"][skill] = progress["skill_counts"].get(skill, 0) + 1
            self._check_skill_upgrade(skill, progress["skill_counts"][skill])

    def _check_skill_upgrade(self, skill: str, count: int):
        """检查技能是否升级"""
        current_level = self.skill_levels.get(skill, SkillLevel.LOCKED)
        if current_level == SkillLevel.BEGINNER and count >= 2:
            self.skill_levels[skill] = SkillLevel.DEVELOPING
        elif current_level == SkillLevel.DEVELOPING and count >= 5:
            self.skill_levels[skill] = SkillLevel.PROFICIENT

    def get_skill_status(self) -> dict:
        """获取技能状态"""
        status = {}
        for skill, level in self.skill_levels.items():
            status[skill] = {
                "level": level.value,
                "label": self._get_level_label(level),
                "progress": self._get_level_progress(level),
            }
        return status

    def _get_level_label(self, level: SkillLevel) -> str:
        labels = {
            SkillLevel.LOCKED: "待解锁",
            SkillLevel.BEGINNER: "初学者",
            SkillLevel.DEVELOPING: "练习中",
            SkillLevel.PROFICIENT: "熟练",
        }
        return labels.get(level, "未知")

    def _get_level_progress(self, level: SkillLevel) -> float:
        if level == SkillLevel.LOCKED:
            return 0.0
        elif level == SkillLevel.BEGINNER:
            return 0.25
        elif level == SkillLevel.DEVELOPING:
            return 0.6
        else:
            return 1.0

    def recommend_training(self, stuck_history: list[str]):
        """基于卡壳历史推荐训练"""
        if not stuck_history:
            return None

        from collections import Counter
        stuck_counts = Counter(stuck_history)
        most_common = stuck_counts.most_common(1)[0]
        stuck_type, count = most_common

        stuck_to_skill = {
            "情节推进卡": "动作描写",
            "细节展开卡": "感官聚焦",
            "过渡衔接卡": "过渡衔接",
            "情感表达卡": "结尾收束",
            "心理描写卡": "心理描写",
        }

        skill = stuck_to_skill.get(stuck_type)
        if skill:
            cards = self.get_skill_training(skill)
            return random.choice(cards) if cards else None
        return None
