"""
智能内容分析引擎 - 自动识别卡壳类型、写作进度、内容密度
"""
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from .state_machine import StuckType


@dataclass
class AnalysisResult:
    """内容分析结果"""
    stuck_type: Optional[StuckType] = None
    stuck_confidence: float = 0.0
    section: str = "开头"  # 开头/中段/结尾
    section_progress: float = 0.0  # 0-1
    content_density: Dict[str, float] = None  # 叙事/描写/对话/心理 密度
    word_count: int = 0
    paragraph_count: int = 0
    emotion_signals: List[Dict] = None  # 情绪信号
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.content_density is None:
            self.content_density = {"narrative": 0, "description": 0, "dialogue": 0, "psychology": 0}
        if self.emotion_signals is None:
            self.emotion_signals = []
        if self.suggestions is None:
            self.suggestions = []


class ContentAnalyzer:
    """内容分析器 - 基于文本特征自动识别"""
    
    # 卡壳类型识别规则
    STUCK_PATTERNS = {
        StuckType.TYPE_2_DETAIL: {
            "patterns": [
                r"[很非常特别十分相当][\u4e00-\u9fa5]{1,3}[的得]",  # 概括性形容词密集
                r"[好看美丽漂亮丑陋巨大很小]",
            ],
            "indicators": ["没有画面感", "不生动", "太笼统"],
            "density_threshold": 0.4,  # 形容词密度阈值
        },
        StuckType.TYPE_3_TRANSITION: {
            "patterns": [
                r"然后[接着|后来|突然]",  # 过渡词后无内容
                r"[时候|那时|接着][\s]*$",  # 以时间词结尾
            ],
            "indicators": ["接不上", "跳跃", "不连贯"],
        },
        StuckType.TYPE_1_PLOT: {
            "patterns": [
                r"(然后|接着|后来)[\s]*[^\u4e00-\u9fa5]",  # 过渡词后内容中断
            ],
            "indicators": ["不知道", "没思路", "接下来"],
        },
        StuckType.TYPE_4_EMOTION: {
            "patterns": [
                r"[觉得感觉感到][\s]*[。，]",  # 情感词后无展开
            ],
            "indicators": ["不会抒情", "怎么点题", "升华"],
        },
        StuckType.TYPE_6_PSYCHOLOGY: {
            "patterns": [
                r"[心想心想觉得][\s]*[^\u4e00-\u9fa5]{0,5}[。，]",  # 心理词后太简短
            ],
            "indicators": ["心理", "内心", "心情"],
        },
    }
    
    # 感官描写词汇
    SENSORY_WORDS = {
        "visual": ["看", "望", "瞧", "瞅", "瞥", "扫", "瞪", "盯", "注视", "凝视", "看见", "望见", "瞅见", "颜色", "红", "绿", "蓝", "白", "黑", "亮", "暗", "光", "影", "形状"],
        "auditory": ["听", "闻", "声响", "声音", "响", "鸣", "叫", "喊", "吵", "静", "喧闹", "寂静", "嗡嗡", "沙沙", "咚咚"],
        "tactile": ["摸", "触", "碰", "感觉", "冰冷", "温暖", "热", "凉", "光滑", "粗糙", "柔软", "坚硬"],
        "olfactory": ["闻", "香", "臭", "味", "气味", "清香", "芳香", "刺鼻"],
        "gustatory": ["尝", "吃", "甜", "酸", "苦", "辣", "咸", "美味", "难吃"],
    }
    
    # 情感相关词汇
    EMOTION_WORDS = ["开心", "快乐", "难过", "伤心", "生气", "愤怒", "害怕", "紧张", "激动", "感动", "温暖", "孤独", "寂寞", "自豪", "羞愧", "后悔", "期待", "失望"]
    
    # 对话标记
    DIALOGUE_MARKS = ['"', '"', '"', '"', "'", "'", "说", "道", "喊", "叫", "问", "回答", "嘀咕", "嘟囔"]
    
    # 心理活动标记
    PSYCHOLOGY_MARKS = ["想", "心想", "觉得", "感觉", "感到", "认为", "意识到", "发现", "明白", "懂得", "才知道", "恍然大悟"]
    
    def analyze(self, text: str, cursor_pos: Optional[int] = None) -> AnalysisResult:
        """分析文本内容"""
        result = AnalysisResult()
        result.word_count = len(text.replace('\n', '').replace(' ', ''))
        result.paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
        
        # 1. 分析写作进度
        result.section, result.section_progress = self._detect_section(text, cursor_pos)
        
        # 2. 分析内容密度
        result.content_density = self._analyze_content_density(text)
        
        # 3. 检测卡壳类型（基于最后一段）
        last_paragraph = self._get_last_paragraph(text, cursor_pos)
        result.stuck_type, result.stuck_confidence = self._detect_stuck_type(last_paragraph, text)
        
        # 4. 检测情绪信号
        result.emotion_signals = self._detect_emotion_signals(text, last_paragraph)
        
        # 5. 生成建议
        result.suggestions = self._generate_suggestions(result)
        
        return result
    
    def _detect_section(self, text: str, cursor_pos: Optional[int] = None) -> Tuple[str, float]:
        """检测当前写作段落和进度"""
        total_chars = len(text.replace('\n', '').replace(' ', ''))
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # 启发式分段
        if total_chars < 100:
            return "开头", total_chars / 150 if total_chars < 150 else 1.0
        
        # 检查结尾标记
        last_100 = text[-100:] if len(text) >= 100 else text
        ending_markers = ["最后", "终于", "结尾", "总之", "总而言之", "综上所述", "明白了", "懂得了", "那一刻"]
        has_ending = any(m in last_100 for m in ending_markers)
        
        # 检查中段标记
        body_markers = ["后来", "接着", "然后", "突然", "正在", "这时", "那一刻之前"]
        has_body = any(m in text for m in body_markers)
        
        if has_ending and total_chars > 400:
            progress = min(total_chars / 650, 1.0)
            return "结尾", progress
        elif has_body or total_chars > 200:
            progress = min((total_chars - 150) / 400, 1.0)
            return "中段", progress
        else:
            progress = min(total_chars / 150, 1.0)
            return "开头", progress
    
    def _analyze_content_density(self, text: str) -> Dict[str, float]:
        """分析叙事/描写/对话/心理的内容密度"""
        if not text:
            return {"narrative": 0, "description": 0, "dialogue": 0, "psychology": 0}
        
        paragraphs = [p for p in text.split('\n') if p.strip()]
        if not paragraphs:
            return {"narrative": 0, "description": 0, "dialogue": 0, "psychology": 0}
        
        total_chars = len(text.replace('\n', ''))
        
        # 叙事：时间词 + 动作动词
        narrative_markers = ["了", "着", "过", "去", "来", "走", "跑", "拿", "放", "看", "站", "坐", "等", "开始", "结束", "完成"]
        narrative_count = sum(text.count(m) for m in narrative_markers)
        
        # 描写：感官词 + 形容词
        sensory_words = []
        for category in self.SENSORY_WORDS.values():
            sensory_words.extend(category)
        description_count = sum(text.count(w) for w in sensory_words)
        
        # 对话：引号 + 说/道
        dialogue_count = sum(text.count(m) for m in self.DIALOGUE_MARKS)
        
        # 心理：心理活动标记
        psychology_count = sum(text.count(m) for m in self.PSYCHOLOGY_MARKS)
        
        # 计算密度（归一化到0-1）
        max_count = max(narrative_count, description_count, dialogue_count, psychology_count, 1)
        
        return {
            "narrative": min(narrative_count / (total_chars * 0.05), 1.0),
            "description": min(description_count / (total_chars * 0.03), 1.0),
            "dialogue": min(dialogue_count / (total_chars * 0.02), 1.0),
            "psychology": min(psychology_count / (total_chars * 0.02), 1.0),
        }
    
    def _get_last_paragraph(self, text: str, cursor_pos: Optional[int] = None) -> str:
        """获取最后一段或光标所在段落"""
        if cursor_pos is not None and cursor_pos > 0:
            # 找到光标所在的段落
            before_cursor = text[:cursor_pos]
            paragraphs = before_cursor.split('\n\n')
            if paragraphs:
                return paragraphs[-1].strip()
        
        # 默认返回最后一段
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        return paragraphs[-1] if paragraphs else text
    
    def _detect_stuck_type(self, last_paragraph: str, full_text: str) -> Tuple[Optional[StuckType], float]:
        """基于最后一段内容检测卡壳类型"""
        if not last_paragraph:
            return StuckType.TYPE_1_PLOT, 0.5
        
        scores = {}
        
        # 规则1: 形容词密度过高 → 描写空洞
        adj_count = len(re.findall(r'[很非常特别十分相当][\u4e00-\u9fa5]{1,3}[的得]', last_paragraph))
        total_chars = len(last_paragraph)
        if total_chars > 0:
            adj_density = adj_count / (total_chars / 10)  # 每10字中形容词个数
            if adj_density > 0.3:
                scores[StuckType.TYPE_2_DETAIL] = adj_density
        
        # 规则2: 以过渡词结尾但无后续 → 情节断层
        transition_ending = re.search(r'(然后|接着|后来|突然)[\s]*[^\u4e00-\u9fa5]{0,3}$', last_paragraph)
        if transition_ending:
            scores[StuckType.TYPE_1_PLOT] = 0.8
        
        # 规则3: 对话占比过高 → 感官缺失
        dialogue_chars = sum(1 for c in last_paragraph if c in '""""')
        if total_chars > 0 and dialogue_chars / total_chars > 0.3:
            if self._has_little_description(last_paragraph):
                scores[StuckType.TYPE_2_DETAIL] = scores.get(StuckType.TYPE_2_DETAIL, 0) + 0.6
        
        # 规则4: 时空词突兀 → 时空混乱
        sudden_time_space = re.search(r'( Suddenly|突然|忽然|刹那间|一瞬间)[\s]*[^\u4e00-\u9fa5]', last_paragraph)
        if sudden_time_space and len(last_paragraph) < 50:
            scores[StuckType.TYPE_3_TRANSITION] = 0.7
        
        # 规则5: 有总结词但事件不足 → 结尾困难
        if total_chars < 30 and any(w in last_paragraph for w in ["总之", "最后", "终于", "明白了"]):
            scores[StuckType.TYPE_4_EMOTION] = 0.75
        
        # 规则6: 心理词后太简短
        psychology_short = re.search(r'(心想|觉得|感到)[\s]*[^\u4e00-\u9fa5]{0,5}[。，]', last_paragraph)
        if psychology_short and len(last_paragraph) < 40:
            scores[StuckType.TYPE_6_PSYCHOLOGY] = 0.7
        
        # 规则7: 段落太短且无描写
        if total_chars < 50 and not self._has_sensory_words(last_paragraph):
            scores[StuckType.TYPE_2_DETAIL] = scores.get(StuckType.TYPE_2_DETAIL, 0) + 0.5
        
        # 选择最高分
        if not scores:
            return StuckType.TYPE_1_PLOT, 0.4  # 默认情节断层
        
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        
        return best_type, min(best_score, 1.0)
    
    def _has_little_description(self, text: str) -> bool:
        """检查是否有很少描写"""
        sensory_count = sum(text.count(w) for w in self.SENSORY_WORDS["visual"])
        return sensory_count < 2
    
    def _has_sensory_words(self, text: str) -> bool:
        """检查是否有感官词"""
        all_sensory = []
        for words in self.SENSORY_WORDS.values():
            all_sensory.extend(words)
        return any(w in text for w in all_sensory)
    
    def _detect_emotion_signals(self, text: str, last_paragraph: str) -> List[Dict]:
        """检测文本中的情绪信号"""
        signals = []
        
        # 信号1: 大量删除（通过文本特征推测）
        if len(last_paragraph) < 20 and len(text) > 200:
            signals.append({
                "type": "delete_burst",
                "severity": "light",
                "indicator": "最后一段过短，可能有删除行为"
            })
        
        # 信号2: 负面词汇
        negative_words = ["不会", "不知道", "太难了", "写不下去", "不想写", "没思路", "卡住了", "太难了"]
        for word in negative_words:
            if word in text:
                signals.append({
                    "type": "negative_text",
                    "severity": "medium" if word in ["太难了", "写不下去", "不想写"] else "light",
                    "indicator": f"检测到负面词汇：{word}"
                })
        
        # 信号3: 重复求助信号（文本中出现多次"怎么"）
        how_count = text.count("怎么")
        if how_count >= 3:
            signals.append({
                "type": "repeated_help",
                "severity": "medium",
                "indicator": f"多次询问'怎么'（{how_count}次）"
            })
        
        # 信号4: 文本混乱度（乱序文字）
        if len(text) > 50:
            # 检查是否有大量重复字符
            repeated_pattern = re.search(r'(.)\1{4,}', text)  # 同一字符重复5次以上
            if repeated_pattern:
                signals.append({
                    "type": "chaotic_text",
                    "severity": "heavy",
                    "indicator": "检测到重复字符，可能有沮丧性乱写"
                })
        
        return signals
    
    def _generate_suggestions(self, result: AnalysisResult) -> List[str]:
        """基于分析结果生成建议"""
        suggestions = []
        
        # 基于进度的建议
        if result.section == "开头" and result.section_progress > 0.5:
            suggestions.append("开头已较完整，建议尽快进入主要事件")
        elif result.section == "中段" and result.content_density["description"] < 0.3:
            suggestions.append("中段可以加入更多细节描写")
        elif result.section == "结尾" and result.section_progress < 0.3:
            suggestions.append("结尾建议控制在3-5句话，不要过长")
        
        # 基于密度的建议
        if result.content_density["dialogue"] > 0.6:
            suggestions.append("对话较多，可以尝试加入场景或动作描写")
        if result.content_density["psychology"] < 0.1 and result.word_count > 200:
            suggestions.append("可以适当加入内心活动，让文章更有深度")
        
        return suggestions
    
    def quick_analyze(self, text: str) -> Dict:
        """快速分析接口，返回简化结果"""
        result = self.analyze(text)
        return {
            "stuck_type": result.stuck_type.value if result.stuck_type else None,
            "stuck_confidence": round(result.stuck_confidence, 2),
            "section": result.section,
            "section_progress": round(result.section_progress, 2),
            "word_count": result.word_count,
            "paragraph_count": result.paragraph_count,
            "content_density": {k: round(v, 2) for k, v in result.content_density.items()},
            "emotion_signals": result.emotion_signals,
            "suggestions": result.suggestions,
        }
