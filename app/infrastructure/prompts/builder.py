"""Prompt 构建器 - 统一管理所有 Prompt 模板"""
import os
from typing import Dict, List, Optional

from core.state_machine import SessionState, TaskMode, GuideLevel, StuckType


class PromptBuilder:
    """
    Prompt 构建器

    职责：
    1. 从 prompts/ 目录加载所有模板文件
    2. 根据 SessionState 动态组装 system + user prompt
    3. 支持模板变量替换

    目录结构：
    prompts/
    ├── system_prompt.md          # 基础系统 prompt
    ├── modes/                    # 各模式模板
    │   ├── topic_analysis.md
    │   ├── stuck_rescue.md
    │   ├── ending_guide.md
    │   └── complete.md
    ├── levels/                   # 各层级指令
    │   ├── L1.md
    │   ├── L2.md
    │   ├── L3.md
    │   └── L4.md
    ├── stuck_types/              # 卡壳类型策略
    │   ├── plot.md
    │   ├── detail.md
    │   ├── transition.md
    │   ├── emotion.md
    │   ├── paragraph.md
    │   └── psychology.md
    └── cooldown/                 # 冷却指令
        ├── active.md
        └── inactive.md
    """

    def __init__(self, prompts_dir: Optional[str] = None):
        if prompts_dir is None:
            prompts_dir = os.path.join(os.path.dirname(__file__), "..", "..", "prompts")
        self.prompts_dir = prompts_dir
        self._cache: Dict[str, str] = {}

    def _load(self, *parts: str) -> str:
        """加载模板文件，带缓存"""
        key = "/".join(parts)
        if key not in self._cache:
            path = os.path.join(self.prompts_dir, *parts)
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    self._cache[key] = f.read()
            else:
                self._cache[key] = ""
        return self._cache[key]

    # === 基础模板 ===

    def system_prompt(self) -> str:
        """基础系统 prompt"""
        return self._load("system_prompt.md")

    # === 模式模板 ===

    def mode_prompt(self, mode: TaskMode) -> str:
        """获取模式模板"""
        mapping = {
            TaskMode.TOPIC_ANALYSIS: "modes/topic_analysis.md",
            TaskMode.STUCK_RESCUE: "modes/stuck_rescue.md",
            TaskMode.ENDING_GUIDE: "modes/ending_guide.md",
            TaskMode.COMPLETE: "modes/complete.md",
        }
        return self._load(mapping.get(mode, "modes/complete.md"))

    # === 层级指令 ===

    def level_instruction(self, level: GuideLevel) -> str:
        """获取层级指令"""
        mapping = {
            GuideLevel.L1_DIRECTION: "levels/L1.md",
            GuideLevel.L2_STRUCTURE: "levels/L2.md",
            GuideLevel.L3_KEYWORDS: "levels/L3.md",
            GuideLevel.L4_EXAMPLES: "levels/L4.md",
        }
        return self._load(mapping.get(level, "levels/L1.md"))

    # === 卡壳类型策略 ===

    def stuck_type_instruction(self, stuck_type: Optional[StuckType]) -> str:
        """获取卡壳类型策略"""
        if not stuck_type:
            return "等待分类器识别卡壳类型。"
        mapping = {
            StuckType.TYPE_1_PLOT: "stuck_types/plot.md",
            StuckType.TYPE_2_DETAIL: "stuck_types/detail.md",
            StuckType.TYPE_3_TRANSITION: "stuck_types/transition.md",
            StuckType.TYPE_4_EMOTION: "stuck_types/emotion.md",
            StuckType.TYPE_5_PARAGRAPH: "stuck_types/paragraph.md",
            StuckType.TYPE_6_PSYCHOLOGY: "stuck_types/psychology.md",
        }
        return self._load(mapping.get(stuck_type, ""))

    # === 冷却指令 ===

    def cooldown_instruction(self, active: bool) -> str:
        """获取冷却指令"""
        if active:
            return self._load("cooldown/active.md")
        return self._load("cooldown/inactive.md")

    def cooldown_status(self, active: bool) -> str:
        """冷却状态文本"""
        return "已激活 - 强制停止给新内容" if active else "未激活"

    # === 组装方法 ===

    def build(self, session: SessionState, user_input: str) -> Dict[str, str]:
        """
        根据会话状态构建完整 prompt

        Returns:
            {"system": str, "user": str}
        """
        mode = session.task_mode

        # 基础 system prompt
        system = self.system_prompt()

        # 模式特定 prompt
        mode_template = self.mode_prompt(mode)

        # 变量替换
        mode_content = self._render_mode_template(mode_template, session)

        # 拼接 system prompt
        system += f"\n\n{mode_content}"

        # 构建 user prompt
        user = self._build_user_prompt(session, user_input)

        return {"system": system, "user": user}

    def _render_mode_template(self, template: str, session: SessionState) -> str:
        """渲染模式模板，替换变量"""
        # 通用变量
        stuck_type_name = session.current_stuck_type.value if session.current_stuck_type else "待识别"
        level_value = session.current_level.value if session.current_level else 1
        cooldown_active = session.should_cool_down()

        # 替换变量
        result = template
        result = result.replace("{stuck_type}", stuck_type_name)
        result = result.replace("{level}", str(level_value))
        result = result.replace("{stuck_count}", str(session.stuck_count))
        result = result.replace("{cooldown_status}", self.cooldown_status(cooldown_active))
        result = result.replace("{cooldown_instruction}", self.cooldown_instruction(cooldown_active))
        result = result.replace("{level_instruction}", self.level_instruction(session.current_level))
        result = result.replace("{stuck_type_instruction}", self.stuck_type_instruction(session.current_stuck_type))

        return result

    def _build_user_prompt(self, session: SessionState, user_input: str) -> str:
        """构建 user prompt（上下文 + 用户输入）"""
        parts: List[str] = []

        # 作文题目
        if session.topic:
            parts.append(f"作文题目：{session.topic}")

        # 已写内容（卡壳/结尾模式时）
        if session.written_content and session.task_mode in (TaskMode.STUCK_RESCUE, TaskMode.ENDING_GUIDE):
            max_len = 600 if session.task_mode == TaskMode.ENDING_GUIDE else 500
            parts.append(f"\n学生已写内容：\n{session.written_content[:max_len]}")

        # 历史对话（审题模式时）
        if session.conversation_history and session.task_mode == TaskMode.TOPIC_ANALYSIS:
            recent = session.conversation_history[-6:]
            parts.append("\n之前的对话：")
            for msg in recent:
                prefix = "学生" if msg["role"] == "user" else "你"
                parts.append(f"{prefix}：{msg['content']}")

        # 用户当前输入
        parts.append(f"\n学生当前输入：{user_input}")

        # 模式特定的指令后缀
        suffix = self._get_user_suffix(session.task_mode)
        if suffix:
            parts.append(suffix)

        return "\n".join(parts)

    def _get_user_suffix(self, mode: TaskMode) -> str:
        """获取 user prompt 后缀"""
        suffixes = {
            TaskMode.TOPIC_ANALYSIS: "\n请根据审题立意策略回复。",
            TaskMode.STUCK_RESCUE: "\n请根据分层引导策略回复。",
            TaskMode.ENDING_GUIDE: "\n请帮助选择结尾策略并给出引导。",
            TaskMode.COMPLETE: "\n请给出简短鼓励。",
        }
        return suffixes.get(mode, "")
