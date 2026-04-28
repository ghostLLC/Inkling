"""LLM Provider 接口 - 支持多种大模型后端
"""
import random
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """LLM提供商抽象基类"""

    @abstractmethod
    def chat(self, system_prompt: str, user_prompt: str, context: str | None = None) -> str:
        """调用LLM进行对话
        
        Args:
            system_prompt: 系统级prompt
            user_prompt: 用户输入prompt
            context: 可选的上下文信息
        
        Returns:
            AI回复文本

        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """提供商名称"""
        pass


class MockProvider(LLMProvider):
    """模拟LLM提供商 - 用于本地演示和测试
    根据Prompt关键词返回预设回复
    """

    def __init__(self):
        self._name = "MockProvider"
        self.responses = self._build_responses()

    @property
    def name(self) -> str:
        return self._name

    def _build_responses(self) -> dict[str, list]:
        """构建模拟回复库"""
        return {
            "topic_analysis": [
                """这个题目有两个关键词值得关注：

1. "那一刻" —— 提示你需要聚焦到一个具体的瞬间，不是一整天，不是一个月，就是那一个场景
2. "长大了" —— 提示这件事要体现你的某种转变或领悟，不是单纯记事

我想先问你：你现在脑子里有没有一个具体的瞬间？哪怕是很小的事。比如第一次独自做什么，或者突然理解了某个人。""",

                """好的，"帮妈妈洗碗"这个方向可以写。接下来我想了解：

那个"长大的瞬间"具体发生了什么？
- 是妈妈说了什么话？
- 是你看到了什么细节？
- 还是你突然感受到了什么？

给我一两个细节就行，不用完整故事。""",

                """📌 起步框架（供参考，不照抄）

开头切入点：
→ 从那个"突然理解"的瞬间直接切入，不必从头讲为什么要洗碗

段落推进提示：
1. → 先写"洗碗之前"你以为这是什么感觉（铺垫）
2. → 再写"那一刻看到了什么"（妈妈的白头发？手？表情？）
3. → 最后写"那一刻之后你的想法"（点题：原来长大不是年龄，是...）

结尾提醒：
→ 回到题目"长大了"，用一句话说出你现在的理解

你可以开始了。写不下去的时候再叫我。"""
            ],

            "stuck_rescue_plot": [
                """你现在卡在情节推进上。接下来有两种常见走向：

1. 事件继续发展，出现新的波折或意外
2. 停下来，描写当前场景的氛围和你自己的感受

你更倾向于哪一种？或者你心里其实有模糊的想法？""",

                """如果要继续推进事件，可以试试这三种方式：

→ 增加一个小意外（比如突然下雨、手机响了、有人出现）
→ 加入另一个人的反应（妈妈的回应？同学的一句话？）
→ 时间推移，环境变化（天色暗了、周围安静了）

你觉得你的故事适合加哪种元素？""",

                """如果要加转折，可以考虑这些关键词：

动作：突然、没想到、正当我...的时候
心理：愣了一下、还没反应过来、下意识

试着在你的场景里找一个"打破预期"的时刻。不是大事，很小的事也可以。""",

                """💡 示例句式（仅供参考，用你的内容替换）：

"正当我以为一切顺利的时候，身后的门突然响了一声。"

注意：这只是句子的骨架，请把你的故事内容填进去。不要整句照抄。

现在建议你先根据刚才的提示，自己试着写2-3句话。写完之后如果还觉得不对，我们再一起看。写作不是一次就写对的，是先写出来再改对的。✍️"""
            ],

            "stuck_rescue_detail": [
                """你现在的段落缺少具体细节。可以从三个维度选一种先丰富：

→ 你看到了什么（视觉）
→ 你听到了什么（听觉）
→ 你身体感受到了什么（触觉/动作）

你想先写哪种感官？""",

                """建议在这段加入：
1个动作细节 + 1个环境细节 + 1个内心反应

这样不会太多，也能让画面立体起来。你现在的段落有哪种？缺哪种？""",

                """视觉词：光线暗了下来、手指在颤抖、背影变小了
听觉词：沉默了几秒、远处传来脚步声、筷子碰碗的声音
触觉词：手心出汗、后背发凉、喉咙发紧

选2-3个放进你的段落里。不用全用。""",

                """💡 示例（仅供参考）：

"我盯着他颤抖的手指，远处传来上课铃声，但我的后背已经湿透。"

试着用你的场景替换关键词。先自己写一版，不管好不好，写出来再说。"""
            ],

            "stuck_rescue_emotion": [
                """你想让读者感受到什么？直接说出感受，还是通过一个细节让读者自己感受到？

初中生记叙文一般用"明示+暗示"结合。你倾向哪种？或者你现在的段落缺的是哪种？""",

                """情感表达通常放在段落的最后1-2句。顺序建议：
做了什么 → 感受到了什么 → 明白了什么

你现在的段落到哪一步了？""",

                """感悟类：我突然意识到、那一刻我才明白、原来...
成长类：我第一次感到、从那以后
感恩类：我从未想过、现在回想

选一个最贴近你感受的，写成一句话。""",

                """💡 示例句式：

"那一刻我才明白，原来他说的那句话，不是为了批评我，而是想让我少走弯路。"

这是"事件+感悟"的结构。换成你的具体内容。先写一版，不用完美。"""
            ],

            "ending_guide": [
                """我读了你的正文，故事已经很完整了。结尾有几种常见的收束方式：

1. 【感悟式】—— 直接说出这件事让你明白了什么（适合成长主题）
2. 【呼应式】—— 回到开头写的那个场景/物件，形成对照
3. 【行动式】—— 结尾不写感悟，而是写你接下来做的一个具体动作

你倾向哪一种？或者你有别的想法？""",

                """感悟式点题方向：
把"那一刻"的具体感受，扩展成"现在回头看"的理解

关键词建议：那一刻、原来、从那以后、我终于明白

提醒：用"我"的感受说，不要变成讲道理。

先试着写，写完再叫我看看方向对不对。""",

                """💡 结尾不用长，3-5句话就够了。

第一句：拉回那个瞬间
第二句：说出你的感受/理解
第三句：点题"长大了"

先试着写，写完再叫我看看方向对不对。"""
            ],

            "cool_down": [
                """💡 我们已经把这一步拆解得比较细了。现在我建议你先根据刚才的提示，自己试着写2-3句话。写完之后如果还觉得不对，我们再一起看。

记住：写作不是一次就写对的，是先写出来再改对的。✍️"""
            ],

            "default": [
                """我理解你的情况。先别急，我们一步一步来。

你可以告诉我：
1. 你现在写到哪一部分了？（开头/中间/结尾）
2. 具体卡在哪里？是不知道写什么，还是不知道怎么写细？

说清楚这两点，我就能给你更准确的帮助。""",

                """这个方向有进展。继续往下写的时候，你可以关注：

→ 当前段落的功能（是铺垫、推进，还是转折？）
→ 下一个段落要交代什么新信息？
→ 有没有一个具体的画面可以写？

先试着自己推进一下，写不出来再叫我。"""
            ]
        }

    def chat(self, system_prompt: str, user_prompt: str, context: str | None = None) -> str:
        """模拟LLM回复
        根据prompt中的关键词匹配预设回复
        优化：使用精确的模式匹配，避免system_prompt中的原则文字干扰
        """
        combined = system_prompt + user_prompt

        # 辅助函数：检查是否处于真正的冷却状态（不是原则文字）
        def _is_real_cooldown():
            # 真正的冷却状态：system_prompt中的"### 冷却机制"后面有实际内容
            # 而不仅仅是空标题
            cooling_section = system_prompt.find("### 冷却机制")
            if cooling_section == -1:
                return False
            # 检查冷却机制标题后面是否有实际内容（非空）
            after_title = system_prompt[cooling_section + len("### 冷却机制"):]
            # 如果后面紧接着就是空行或下一个标题，说明没有实际冷却内容
            stripped = after_title.strip()
            if not stripped or stripped.startswith("###"):
                return False
            return True

        # 1. 检查具体模式 - 使用更精确的匹配
        # 审题立意模式
        is_topic_analysis = (
            ("审题立意" in system_prompt or "TOPIC_ANALYSIS" in system_prompt)
            and "卡壳救援" not in system_prompt
            and "## 当前模式：写作中途卡壳救援" not in system_prompt
        )

        # 卡壳救援模式
        is_stuck_rescue = (
            ("卡壳救援" in system_prompt or "STUCK_RESCUE" in system_prompt
             or "## 当前模式：写作中途卡壳救援" in system_prompt)
            and "结尾收束" not in system_prompt
            and "## 当前模式：结尾收束" not in system_prompt
        )

        # 结尾收束模式
        is_ending_guide = (
            "结尾收束" in system_prompt or "ENDING_GUIDE" in system_prompt
             or "## 当前模式：结尾收束" in system_prompt
        )

        if is_topic_analysis:
            # 判断是第几轮
            if "之前的对话" in user_prompt:
                # 有历史对话，不是第一轮
                if "有没有一个具体的瞬间" in combined or "帮妈妈" in user_prompt:
                    return random.choice(self.responses["topic_analysis"][1:2])
                return random.choice(self.responses["topic_analysis"][2:3])
            return random.choice(self.responses["topic_analysis"][:2])

        if is_stuck_rescue:
            # 判断是否应该返回冷却回复
            should_cool = _is_real_cooldown() and "L4" in system_prompt

            # 判断卡壳类型
            if "情节推进" in system_prompt or "TYPE_1" in system_prompt or "TYPE_1_PLOT" in system_prompt:
                if should_cool:
                    return random.choice(self.responses["cool_down"])
                return self._pick_by_level(self.responses["stuck_rescue_plot"], system_prompt)

            if "细节展开" in system_prompt or "TYPE_2" in system_prompt or "TYPE_2_DETAIL" in system_prompt:
                if should_cool:
                    return random.choice(self.responses["cool_down"])
                return self._pick_by_level(self.responses["stuck_rescue_detail"], system_prompt)

            if "情感表达" in system_prompt or "TYPE_4" in system_prompt or "TYPE_4_EMOTION" in system_prompt:
                if should_cool:
                    return random.choice(self.responses["cool_down"])
                return self._pick_by_level(self.responses["stuck_rescue_emotion"], system_prompt)

            # 默认卡壳回复
            if should_cool:
                return random.choice(self.responses["cool_down"])
            return random.choice(self.responses["default"])

        if is_ending_guide:
            # 判断用户意图
            if "感悟" in user_prompt or "感悟式" in user_prompt:
                return self.responses["ending_guide"][1]
            elif "呼应" in user_prompt or "呼应式" in user_prompt:
                return self.responses["ending_guide"][1]  # 暂时复用
            elif "行动" in user_prompt or "行动式" in user_prompt:
                return self.responses["ending_guide"][1]  # 暂时复用
            return random.choice(self.responses["ending_guide"])

        # 兜底：只有在明确有冷却内容时才返回冷却回复
        if _is_real_cooldown():
            return random.choice(self.responses["cool_down"])

        return random.choice(self.responses["default"])

    def _pick_by_level(self, responses: list, prompt: str) -> str:
        """根据层级选择回复"""
        # 匹配层级：L1, L2, L3, L4 或 层级：1, 2, 3, 4
        if ("L1" in prompt or "层级：1" in prompt or "层级:1" in prompt or "层级： 1" in prompt) and len(responses) > 0:
            return responses[0]
        elif ("L2" in prompt or "层级：2" in prompt or "层级:2" in prompt or "层级： 2" in prompt) and len(responses) > 1:
            return responses[1]
        elif ("L3" in prompt or "层级：3" in prompt or "层级:3" in prompt or "层级： 3" in prompt) and len(responses) > 2:
            return responses[2]
        elif ("L4" in prompt or "层级：4" in prompt or "层级:4" in prompt or "层级： 4" in prompt) and len(responses) > 3:
            return responses[3]
        return random.choice(responses)


class MoonshotProvider(LLMProvider):
    """Moonshot AI (Kimi) 提供商
    需要配置 API Key
    """

    def __init__(self, api_key: str, model: str = "kimi-k2p5", base_url: str = "https://api.moonshot.cn/v1"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self._name = f"Moonshot-{model}"

    @property
    def name(self) -> str:
        return self._name

    def chat(self, system_prompt: str, user_prompt: str, context: str | None = None) -> str:
        """调用 Moonshot API
        """
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=800
            )

            return response.choices[0].message.content
        except ImportError:
            raise ImportError("使用 MoonshotProvider 需要安装 openai SDK: pip install openai")
        except Exception as e:
            return f"[API 调用失败: {str(e)}] 请检查 API Key 和网络连接。"


class OpenAICompatibleProvider(LLMProvider):
    """通用 OpenAI-compatible 提供商
    支持任意兼容 OpenAI API 格式的后端（如第三方代理、自建服务等）
    """

    def __init__(self, api_key: str, model: str, base_url: str):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self._name = f"OpenAI-Compatible-{model}"

    @property
    def name(self) -> str:
        return self._name

    def chat(self, system_prompt: str, user_prompt: str, context: str | None = None) -> str:
        """调用 OpenAI-compatible API
        """
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=800
            )

            return response.choices[0].message.content
        except ImportError:
            raise ImportError("使用 OpenAICompatibleProvider 需要安装 openai SDK: pip install openai")
        except Exception as e:
            return f"[API 调用失败: {str(e)}] 请检查 API Key、Base URL 和网络连接。"


def create_provider(provider_type: str = "mock", **kwargs) -> LLMProvider:
    """工厂函数，创建LLM提供商
    
    Args:
        provider_type: 提供商类型 (mock/moonshot/openai-compatible)
        **kwargs: 额外参数（如api_key, model, base_url）
    
    Returns:
        LLMProvider实例

    """
    if provider_type == "mock":
        return MockProvider()
    elif provider_type == "moonshot":
        api_key = kwargs.get("api_key", "")
        model = kwargs.get("model", "kimi-k2p5")
        base_url = kwargs.get("base_url", "https://api.moonshot.cn/v1")
        return MoonshotProvider(api_key, model, base_url)
    elif provider_type == "openai-compatible":
        api_key = kwargs.get("api_key", "")
        model = kwargs.get("model", "gpt-4")
        base_url = kwargs.get("base_url", "https://api.openai.com/v1")
        return OpenAICompatibleProvider(api_key, model, base_url)
    else:
        raise ValueError(f"不支持的提供商类型: {provider_type}")
