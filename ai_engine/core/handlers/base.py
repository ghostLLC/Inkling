"""模式处理器基类"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from ..state_machine import SessionState, TaskMode


class ModeHandler(ABC):
    """模式处理器基类
    
    职责：处理特定 TaskMode 下的用户输入，判断状态流转，
    返回是否需要 LLM 生成回复。
    """
    
    @property
    @abstractmethod
    def mode(self) -> TaskMode:
        """该处理器负责的模式"""
        pass
    
    @abstractmethod
    def handle(self, session: SessionState, user_input: str) -> Dict[str, Any]:
        """
        处理用户输入
        
        Returns:
            {
                "ai_response": str | None,      # 固定回复（不需要 LLM 时）
                "requires_llm": bool,             # 是否需要 LLM 生成回复
                "transferred_to": TaskMode | None, # 状态流转目标模式
                "status": str,                    # "ok" / "error"
            }
        """
        pass
    
    def _extract_topic(self, text: str) -> str:
        """从用户输入中提取作文题目"""
        if "《" in text and "》" in text:
            start = text.find("《") + 1
            end = text.find("》", start)
            return text[start:end]
        return text.strip()
