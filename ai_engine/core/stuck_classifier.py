"""卡壳类型分类器 - 基于规则和关键词识别6种卡壳类型
"""
from .state_machine import StuckType


class StuckClassifier:
    """卡壳类型分类器"""

    # 各类型关键词映射
    KEYWORDS = {
        StuckType.TYPE_1_PLOT: [
            "不知道写什么了", "后面怎么写", "接下来呢", "接下来", "接下来写什么",
            "不知道该怎么继续", "不知道怎么继续", "不知道怎么往下", "不知道怎么接",
            "写不下去了", "没思路了", "不知道怎么发展",
            "故事怎么继续", "情节怎么推进", "不知道发生什么", "然后怎么办",
            "不知道怎么写下去", "不知道怎么继续写"
        ],
        StuckType.TYPE_2_DETAIL: [
            "不知道怎么描写", "太笼统了", "怎么写细一点", "怎么写具体",
            "怎么展开", "不够详细", "细节怎么写", "画面感", "描写",
            "怎么写得生动", "怎么加细节", "不知道怎么描述", "不够具体"
        ],
        StuckType.TYPE_3_TRANSITION: [
            "怎么连接", "过渡", "接不起来", "衔接", "怎么过渡", "上下段",
            "段落之间", "怎么接", "怎么连", "前后", "转折", "怎么转"
        ],
        StuckType.TYPE_4_EMOTION: [
            "不知道怎么抒情", "怎么点题", "怎么升华", "情感怎么写",
            "感受怎么表达", "不会写感悟", "怎么写感想", "主题怎么写",
            "怎么写想法", "怎么表达心情", "不会写感受", "怎么收尾"
        ],
        StuckType.TYPE_5_PARAGRAPH: [
            "这段写什么", "这一段怎么安排", "这一段写什么",
            "段落结构", "段落怎么写", "这一段", "这段怎么", "中间怎么写"
        ],
        StuckType.TYPE_6_PSYCHOLOGY: [
            "心理描写", "内心想法", "不知道怎么写心情", "心理活动",
            "内心", "怎么想", "心理", "心情怎么写", "内心感受",
            "想法怎么写", "心理变化", "内心独白"
        ],
    }

    # 结尾相关关键词（用于判断是否要进入结尾模块）
    ENDING_KEYWORDS = [
        "结尾", "不会结尾", "怎么结尾", "怎么收束", "怎么收尾",
        "最后一段", "结尾怎么写", "不知道怎么结束", "不会收尾",
        "不会结尾", "结尾卡了", "最后怎么写"
    ]

    def __init__(self):
        self.keywords = self.KEYWORDS
        self.ending_keywords = self.ENDING_KEYWORDS

    def classify(self, user_input: str, written_content: str = "") -> tuple[StuckType | None, float]:
        """分类卡壳类型
        返回: (卡壳类型, 置信度)
        """
        user_input = user_input.lower()

        # 首先检查是否是结尾相关
        if self._contains_any(user_input, self.ending_keywords):
            return None, -1.0  # 返回特殊标记，表示应进入结尾模块

        # 计算各类型匹配度
        scores = {}
        for stuck_type, keywords in self.keywords.items():
            score = self._calculate_score(user_input, keywords)
            scores[stuck_type] = score

        # 同时考虑已写内容的长度来辅助判断
        if written_content:
            content_length = len(written_content.strip())
            if content_length > 200 and self._contains_any(user_input, ["怎么写"]):
                # 如果已经写了很多，但还在问"怎么写"，可能是细节展开卡
                if scores.get(StuckType.TYPE_2_DETAIL, 0) > 0:
                    scores[StuckType.TYPE_2_DETAIL] += 0.5

        # 选择最高分
        if not scores:
            return None, 0.0

        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]

        # 如果最高分太低，返回未知
        if best_score < 0.3:
            return None, best_score

        return best_type, best_score

    def _calculate_score(self, text: str, keywords: list) -> float:
        """计算文本与关键词集合的匹配度"""
        matched = 0
        for keyword in keywords:
            if keyword in text:
                matched += 1
        # 归一化分数
        return min(matched / 2, 1.0)  # 匹配2个关键词即满分

    def _contains_any(self, text: str, keywords: list) -> bool:
        """检查文本是否包含任意关键词"""
        return any(keyword in text for keyword in keywords)

    def get_type_description(self, stuck_type: StuckType) -> str:
        """获取卡壳类型的描述"""
        descriptions = {
            StuckType.TYPE_1_PLOT: "情节推进卡 - 不知道故事接下来怎么发展",
            StuckType.TYPE_2_DETAIL: "细节展开卡 - 不会写具体画面",
            StuckType.TYPE_3_TRANSITION: "过渡衔接卡 - 两段之间接不上",
            StuckType.TYPE_4_EMOTION: "情感表达卡 - 不会表达感受/主题",
            StuckType.TYPE_5_PARAGRAPH: "段落结构卡 - 不知道这段该承担什么功能",
            StuckType.TYPE_6_PSYCHOLOGY: "心理描写卡 - 不会写内心活动",
        }
        return descriptions.get(stuck_type, "未知卡壳类型")
