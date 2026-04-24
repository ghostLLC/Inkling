"""
内容安全过滤模块 v2
更精确的"代替完成"检测 + 智能降级策略
"""
import re
from typing import Tuple, Optional


class ContentGuard:
    """
    内容安全过滤器 v2
    
    设计原则：
    1. System Prompt 是第一道防线（约束模型输出）
    2. ContentGuard 是最后一道防线（只拦截严重越界）
    3. 轻微越界 → 截断处理，不拦截
    4. 严重越界 → 拦截 + 尝试重生成
    """
    
    # 敏感词列表（仅用于本地输入检查，检测学生是否输入了不适当内容）
    # 这些词不会发送给任何大模型API
    SENSITIVE_WORDS = [
        "暴力", "血腥", "恐怖", "歧视"
    ]
    
    # 检测是否要求代替完成（用户输入）
    CHEATING_PATTERNS = [
        r"帮我写[一]?[篇]?[整]?[全]?.*作文",
        r"直接[给]?[我]?写",
        r"[替代]我写",
        r"写[一]?[篇]?完整[的]?",
        r"直接[输出]?[生成]?.*段落",
    ]
    
    # 输出拦截：严重越界信号（可被直接复制提交的完整作文）
    # 特征：连贯叙述 + 第一人称 + 明显场景描写 + 超过一定长度
    SERIOUS_VIOLATION_PATTERNS = [
        # 完整开头段特征
        r"(记得|那年|那天|小时候|有一次|那是一个).*?[,，。].*?[，。].*?[，。]",
        # 完整叙事段特征（时间+地点+人物+事件）
        r"(那天|那天下午|周末|放学).*?，.*?我.*?和.*?一起.*?[，。]",
        # 抒情段特征
        r"(那一刻|那一刻|那一瞬间|当我|直到).*?，.*?我.*?[，。].*?[，。]",
    ]
    
    # 安全标记——有这些标记的段落几乎不可能是代替完成
    SAFE_MARKERS = ['→', '📌', '💡', '1.', '2.', '3.', '【', '】', '？', '?', '：', ':']
    
    def __init__(self):
        self.sensitive_words = self.SENSITIVE_WORDS
        self.cheating_patterns = [re.compile(p) for p in self.CHEATING_PATTERNS]
        self.serious_patterns = [re.compile(p) for p in self.SERIOUS_VIOLATION_PATTERNS]
    
    def check_input(self, text: str) -> Tuple[bool, str]:
        """
        检查用户输入是否安全
        返回: (是否安全, 原因)
        """
        # 检查敏感词
        for word in self.sensitive_words:
            if word in text:
                return False, "输入内容包含不适当关键词，请重新输入。"
        
        # 检测是否要求代替完成
        for pattern in self.cheating_patterns:
            if pattern.search(text):
                return False, "我只能帮你找回写作思路，不能直接替你写作文哦。说说你卡在哪里了？"
        
        return True, ""
    
    def check_output(self, text: str) -> Tuple[bool, Optional[str], str]:
        """
        检查AI输出是否符合安全规范 v2
        
        返回: (是否通过, 修正后的文本或None, 原因)
        
        策略：
        - 通过 → (True, text, "")
        - 轻微越界 → (True, truncated_text, "截断提示") 
        - 严重越界 → (False, None, "原因")
        """
        # 先检查是否是严重越界（完整作文段落）
        if self._is_serious_violation(text):
            return False, None, "检测到完整作文段落输出，触发安全拦截。"
        
        # 检查是否包含过多可被复制的内容
        truncated = self._truncate_risky_content(text)
        if truncated != text:
            return True, truncated, "已自动截断可能越界的内容"
        
        return True, text, ""
    
    def _is_serious_violation(self, text: str) -> bool:
        """
        检测严重越界：输出可被直接作为作文提交的完整段落
        
        判定标准（需同时满足）：
        1. 总长度 > 300 字符
        2. 不包含任何安全标记（→ 📌 💡 等）
        3. 包含至少2个严重越界模式匹配
        4. 文本连贯（段落之间逻辑衔接，不是列表）
        """
        # 快速排除：如果包含安全标记，几乎不可能是代替完成
        if any(marker in text for marker in self.SAFE_MARKERS):
            return False
        
        # 长度检查
        if len(text) < 300:
            return False
        
        # 检查严重越界模式
        match_count = sum(1 for p in self.serious_patterns if p.search(text))
        if match_count < 2:
            return False
        
        # 检查连贯性：段落之间没有明显的列表/选项分隔
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        list_indicators = sum(1 for l in lines if l.startswith(('1.', '2.', '3.', '-', '→', '•')))
        if len(lines) > 0 and list_indicators / len(lines) < 0.3:
            # 列表/选项占比低于30%，说明是连贯叙述而非引导
            return True
        
        return False
    
    def _truncate_risky_content(self, text: str) -> str:
        """
        截断可能越界的内容（轻微越界处理）
        
        策略：
        - 如果检测到连续叙述超过 250 字符且无安全标记，截断到最近的安全点
        - 截断后添加提示
        """
        paragraphs = text.split('\n\n')
        result = []
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 检查这个段落是否风险较高
            has_safe = any(m in para for m in self.SAFE_MARKERS)
            is_question = '？' in para or '?' in para
            is_example = para.startswith(('💡', '📌', '示例', '注意', '提醒'))
            
            # 风险判断
            if len(para) > 250 and not has_safe and not is_question and not is_example:
                # 截断到 200 字符左右，保留完整性
                truncated = para[:200]
                # 尽量在句尾截断
                for end_char in ['。', '，', '；', '.', ',', ' ']:
                    last_pos = truncated.rfind(end_char)
                    if last_pos > 150:
                        truncated = truncated[:last_pos + 1]
                        break
                result.append(truncated + "...")
                result.append("（提示：刚才的回复有点长，聚焦当前这一步就好。继续写，有问题再叫我。）")
            else:
                result.append(para)
        
        return '\n\n'.join(result)
    
    def sanitize_for_display(self, text: str) -> str:
        """
        清理输出文本，确保适合初中生阅读
        """
        # 移除markdown表格语法
        lines = text.split('\n')
        cleaned = []
        for line in lines:
            if '|' in line and not line.startswith('→'):
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if parts and not all(c in '-|: ' for c in line):
                    cleaned.append('  '.join(parts))
            else:
                cleaned.append(line)
        return '\n'.join(cleaned)
    
    def get_regeneration_prompt(self, violation_reason: str, original_prompt: dict) -> dict:
        """
        生成用于让LLM重新生成的Prompt
        """
        system_addition = f"""
⚠️ 上一轮回复被安全系统拦截，原因：{violation_reason}

请按照以下约束重新回复：
1. 不要输出完整句子或段落
2. 只提供方向、选项、关键词
3. 每条提示不超过20字
4. 用 "→" 标记选项，用 "📌" 标记关键提示
"""
        
        return {
            "system": original_prompt.get("system", "") + system_addition,
            "user": original_prompt.get("user", "")
        }


class OutputLimiter:
    """输出限制器"""
    
    MAX_OUTPUT_LENGTH = 500  # 最大输出字符数
    MAX_EXAMPLE_SENTENCES = 2  # 最大示例句数量
    
    def limit_output(self, text: str) -> str:
        """
        限制输出长度
        """
        if len(text) > self.MAX_OUTPUT_LENGTH:
            # 截断并添加提示
            text = text[:self.MAX_OUTPUT_LENGTH] + "\n\n...（提示已精简，聚焦当前这一步即可）"
        return text
    
    def count_example_sentences(self, text: str) -> int:
        """
        统计示例句数量
        """
        examples = re.findall(r'示例[：:].*?[。.\n]', text)
        return len(examples)
