"""
引导生成器 - 组装Prompt并生成AI回复
"""
import os
from typing import Dict, List, Optional
from .state_machine import SessionState, TaskMode, GuideLevel, StuckType


class GuideGenerator:
    """分层引导生成器"""
    
    def __init__(self, prompts_dir: Optional[str] = None):
        if prompts_dir is None:
            prompts_dir = os.path.join(os.path.dirname(__file__), "..", "prompts")
        self.prompts_dir = prompts_dir
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """加载系统Prompt"""
        path = os.path.join(self.prompts_dir, "system_prompt.md")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        # 默认系统Prompt
        return """你是初中生的写作陪练助手，名字叫"写作小救星"。
你的任务是在学生写作卡壳时，通过分层引导帮助其恢复思路、继续独立完成作文。
请不要直接输出超过2个完整示例句，不要直接续写学生的正文段落。
"""
    
    def generate(self, session: SessionState, user_input: str, llm_response: Optional[str] = None) -> Dict:
        """
        根据会话状态生成完整的Prompt
        返回: {"system": str, "user": str, "context": str}
        """
        mode = session.task_mode
        
        if mode == TaskMode.TOPIC_ANALYSIS:
            return self._generate_topic_prompt(session, user_input)
        elif mode == TaskMode.STUCK_RESCUE:
            return self._generate_stuck_prompt(session, user_input)
        elif mode == TaskMode.ENDING_GUIDE:
            return self._generate_ending_prompt(session, user_input)
        else:
            return self._generate_complete_prompt(session, user_input)
    
    def _generate_topic_prompt(self, session: SessionState, user_input: str) -> Dict:
        """生成审题立意阶段的Prompt"""
        system = self.system_prompt + """

## 当前模式：审题立意辅助
你正在帮助学生理解作文题目，找到写作方向。

### 工作方式
1. 先分析题目关键词（如"那一刻，我长大了"中的"那一刻"和"长大了"）
2. 通过提问引导学生思考，不要直接给完整立意
3. 提供2-3个角度选项供学生选择
4. 最终输出一个"起步框架"（不是提纲，是启动包）

### 追问策略
每次问1-2个问题，根据学生回答动态调整：
- 学生有具体想法 → 顺着深化细节
- 学生思路模糊 → 提供角度选项
- 学生完全没思路 → 提供"生活场景库"（家庭/校园/社会）

### 起步框架格式
📌 起步框架（供参考，不照抄）
开头切入点：→ ...
段落推进提示：
1. → ...
2. → ...
3. → ...
结尾提醒：→ ...
"""
        
        # 构建用户上下文
        context = f"作文题目：{session.topic}\n" if session.topic else ""
        if session.conversation_history:
            # 添加最近几轮对话作为上下文
            recent = session.conversation_history[-6:]
            context += "\n之前的对话：\n"
            for msg in recent:
                prefix = "学生" if msg["role"] == "user" else "你"
                context += f"{prefix}：{msg['content']}\n"
        
        user_prompt = f"{context}\n学生当前输入：{user_input}\n\n请根据审题立意策略回复。"
        
        return {"system": system, "user": user_prompt}
    
    def _generate_stuck_prompt(self, session: SessionState, user_input: str) -> Dict:
        """生成卡壳救援阶段的Prompt"""
        stuck_type = session.current_stuck_type
        level = session.current_level
        
        system = self.system_prompt + f"""

## 当前模式：写作中途卡壳救援
学生已经在写作过程中卡住了，需要帮助其恢复思路。

### 当前状态
- 卡壳类型：{stuck_type.value if stuck_type else "待识别"}
- 当前引导层级：{level.value}（共4层）
- 当前卡壳点已求助次数：{session.stuck_count}

### 引导层级规则
{"""根据当前层级，只提供对应级别的帮助：
""" + self._get_level_instruction(level)}

### 冷却机制（当前状态：{'已激活 - 强制停止给新内容' if session.should_cool_down() else '未激活'}）
{"""💡 冷却状态已激活。学生已求助3次以上。必须停止提供任何新内容。
只允许回复以下固定冷却语（一字不改）：

💡 我们已经把这一步拆解得比较细了。建议你先根据刚才的提示，自己试着写2-3句话。写完之后如果还觉得不对，我们再一起看。写作不是一次就写对的，是先写出来再改对的。✍️

请不要：提供新的方向、结构、关键词或示例句。
请不要：追问学生新的问题。""" if session.should_cool_down() else """如果学生求助达到3次，请切换到冷却模式，暂停给新内容。"""}

### 卡壳类型处理策略
{self._get_stuck_type_instruction(stuck_type)}
"""
        
        context = f"作文题目：{session.topic}\n\n" if session.topic else ""
        if session.written_content:
            context += f"学生已写内容：\n{session.written_content[:500]}\n\n"  # 限制长度
        
        user_prompt = f"{context}学生卡壳描述：{user_input}\n\n请根据分层引导策略回复。"
        
        return {"system": system, "user": user_prompt}
    
    def _generate_ending_prompt(self, session: SessionState, user_input: str) -> Dict:
        """生成结尾收束阶段的Prompt"""
        system = self.system_prompt + """

## 当前模式：结尾收束辅助
学生正文已写完，需要帮助其完成结尾。

### 工作方式
1. 先判断正文是否确实完整（事件是否已讲完）
2. 提供5种结尾策略供选择：感悟式、呼应式、留白式、行动式、对话式
3. 学生选择后，提供点题方向和关键词
4. 不提供完整结尾段落

### 结尾策略库
- 感悟式：直接说出这件事让你明白了什么（适合成长主题）
- 呼应式：回到开头的场景/物件，形成对照
- 留白式：用一个画面结束，不说破感受（初中生慎用）
- 行动式：写事件之后做的第一个具体动作
- 对话式：用一句关键对话收束全文

### 点题提醒
结尾3-5句话即可，不要写太长。重点是把"点题"的那句话说清楚。
"""
        
        context = f"作文题目：{session.topic}\n\n学生已写全文：\n{session.written_content[:600]}\n\n"
        user_prompt = f"{context}学生当前需求：{user_input}\n\n请帮助选择结尾策略并给出引导。"
        
        return {"system": system, "user": user_prompt}
    
    def _generate_complete_prompt(self, session: SessionState, user_input: str) -> Dict:
        """生成写作完成后的Prompt"""
        system = self.system_prompt + "\n\n学生已完成写作，提供轻量鼓励即可。"
        user_prompt = f"学生说：{user_input}\n\n请给出简短鼓励。"
        return {"system": system, "user": user_prompt}
    
    def _get_level_instruction(self, level: GuideLevel) -> str:
        """获取指定层级的指令"""
        instructions = {
            GuideLevel.L1_DIRECTION: """
L1 - 方向引导（严格限制）：
只提供2-3个展开方向或判断建议，用问句或选项呈现。
请不要给：结构安排、具体词语、示例句、句式模板。
每条方向不超过15字。""",
            GuideLevel.L2_STRUCTURE: """
L2 - 结构提示（严格限制）：
在学生确定方向后，提供段落内部的功能安排。
例如"这一段可以分为：现状→变化→你的反应"。
请不要给：具体词语、示例句、句式模板。""",
            GuideLevel.L3_KEYWORDS: """
L3 - 关键词启发（严格限制）：
只提供2-4个零散的词语或短词组，每个不超过4个字。
格式建议用纯词语列表，例如：突然、愣住、原来、才明白。

请避免：组成例句、给句式模板、给填空式句子、用问句代替词语。
请不要输出任何超过5个字的短语。
请不要说"试试用这些词"，直接把词语列出来即可。""",
            GuideLevel.L4_EXAMPLES: """
L4 - 示例句（严格限制）：
最多提供1个不完整的句式骨架，必须留空让学生填自己的内容。
例如："那一刻，我才明白，原来____"。
请注明"这是骨架，用你的内容填空，不要照搬"。
请不要给可直接照搬的完整句子。""",
        }
        return instructions.get(level, "")
    
    def _get_cooldown_instruction(self) -> str:
        """获取冷却指令"""
        return """
💡 冷却状态激活（强制）：
学生已在此卡壳点求助3次以上。必须停止提供任何新内容。
只允许回复以下内容（一字不改）：

💡 我们已经把这一步拆解得比较细了。建议你先根据刚才的提示，自己试着写2-3句话。写完之后如果还觉得不对，我们再一起看。写作不是一次就写对的，是先写出来再改对的。✍️

请不要：提供新的方向、结构、关键词或示例句。
请不要：追问学生新的问题。
请不要：解释或展开之前的提示。
"""
    
    def _get_stuck_type_instruction(self, stuck_type: Optional[StuckType]) -> str:
        """获取指定卡壳类型的处理策略"""
        if not stuck_type:
            return "等待分类器识别卡壳类型。"
        
        instructions = {
            StuckType.TYPE_1_PLOT: """
【情节推进卡】
L1：问"接下来适合推进事件、补细节，还是收束情感？"
L2：提供2-3个推进选项（增加转折/加入他人反应/环境变化）
L3：提供转折词、时间推移词
L4：提供转折句式模板""",
            StuckType.TYPE_2_DETAIL: """
【细节展开卡】
L1：问"缺少哪类细节？视觉/听觉/触觉/动作？"
L2：建议"1个动作细节+1个环境细节+1个内心反应"
L3：提供感官词汇列表
L4：提供感官描写句式""",
            StuckType.TYPE_3_TRANSITION: """
【过渡衔接卡】
L1：问"两段之间是时间推进/场景切换/情感转折/因果推进？"
L2：给出过渡句功能建议
L3：提供过渡词（时间/转折/因果）
L4：提供过渡句式模板""",
            StuckType.TYPE_4_EMOTION: """
【情感表达卡】
L1：问"想用明示还是暗示？"
L2：建议"事件→感受→明白"的顺序
L3：提供感悟类/成长类/感恩类关键词
L4：提供"事件+感悟"句式""",
            StuckType.TYPE_5_PARAGRAPH: """
【段落结构卡】
L1：问"这段承担什么功能？铺垫/推进/转折/高潮？"
L2：给出对应段落内部结构
L3：提供不同功能的写法提示
L4：提供对应功能的示例句""",
            StuckType.TYPE_6_PSYCHOLOGY: """
【心理描写卡】
L1：问"哪种心理状态？紧张/矛盾/意外/感动？"
L2：建议展开方式：身体反应/想法闪回/假设想象/注意力转移
L3：提供具体心理描写词汇
L4：提供"身体反应代替直接说心情"的句式""",
        }
        return instructions.get(stuck_type, "")
