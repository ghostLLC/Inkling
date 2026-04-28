"""
安全检查流水线 - 封装输入/输出安全检查与重生成逻辑
"""
from typing import Tuple, Optional, Dict, Any

from ..content_guard import ContentGuard
from ..llm_provider import LLMProvider


class SecurityPipeline:
    """
    安全检查流水线

    职责：
    1. 输入安全检查
    2. 输出安全检查 + 截断处理
    3. 严重越界时的重新生成
    """

    def __init__(self, content_guard: ContentGuard, llm: LLMProvider):
        self.guard = content_guard
        self.llm = llm

    def check_input(self, text: str) -> Tuple[bool, str]:
        """检查用户输入是否安全"""
        return self.guard.check_input(text)

    def process_output(
        self,
        raw_response: str,
    ) -> Tuple[bool, str, str]:
        """
        处理LLM原始输出

        返回: (是否通过, 处理后的文本, 状态: "ok" | "warning")
        """
        is_valid, processed, reason = self.guard.check_output(raw_response)
        if not is_valid:
            return False, raw_response, reason
        # 截断风险内容
        processed = self.guard._truncate_risky_content(processed)
        return True, processed, "ok"

    def regenerate_safe_response(
        self,
        violation_reason: str,
        original_prompt: Dict[str, str],
    ) -> str:
        """
        尝试重新生成安全回复

        如果重生成仍失败，返回兜底安全提示。
        """
        regen_prompt = self.guard.get_regeneration_prompt(
            violation_reason, original_prompt
        )
        regen_response = self.llm.chat(
            regen_prompt["system"], regen_prompt["user"]
        )

        is_valid2, processed2, _ = self.guard.check_output(regen_response)
        if is_valid2:
            return processed2

        # 二次失败，返回兜底安全提示
        return (
            "我刚才想帮你，但好像说得太多了。换个方式："
            "你现在写到哪一步了？卡在哪里？"
        )
