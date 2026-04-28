"""
LLM 编排器 - 封装 Prompt 生成、LLM 调用与结果处理
"""
from typing import Dict, Any, Optional

from ..guide_generator import GuideGenerator
from ..llm_provider import LLMProvider
from .security_pipeline import SecurityPipeline


class LLMOrchestrator:
    """
    LLM 调用编排器

    职责：
    1. 根据会话状态生成 Prompt
    2. 调用 LLM 获取回复
    3. 安全检查 + 长度限制
    4. 失败时重试/兜底
    """

    def __init__(
        self,
        guide_generator: GuideGenerator,
        security_pipeline: SecurityPipeline,
        llm: LLMProvider,
    ):
        self.guide = guide_generator
        self.security = security_pipeline
        self.llm = llm

    def generate_response(
        self,
        session,
        user_input: str,
    ) -> Dict[str, Any]:
        """
        生成AI回复（完整流程）

        返回: {"ai_response": str, "status": "ok" | "warning"}
        """
        prompt = self.guide.generate(session, user_input)
        ai_response = self.llm.chat(prompt["system"], prompt["user"])

        # 输出安全检查
        is_valid, processed, reason = self.security.process_output(ai_response)
        if not is_valid:
            ai_response = self.security.regenerate_safe_response(reason, prompt)
            status = "warning"
        else:
            ai_response = processed
            status = "ok"

        return {"ai_response": ai_response, "status": status}

    def generate_response_safe(
        self,
        session,
        user_input: str,
    ) -> str:
        """
        生成AI回复（只返回文本，不返回状态）

        失败时返回兜底提示。
        """
        result = self.generate_response(session, user_input)
        return result["ai_response"]
