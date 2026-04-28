"""
StuckClassifier 单元测试
"""
import pytest
from ai_engine.core.stuck_classifier import StuckClassifier, StuckType


class TestStuckClassifier:
    """测试卡壳分类器"""

    def test_classify_plot_stuck(self):
        classifier = StuckClassifier()
        stuck_type, keywords = classifier.classify(
            "我不知道接下来该怎么写了", ""
        )
        assert stuck_type == StuckType.TYPE_1_PLOT

    def test_classify_detail_stuck(self):
        classifier = StuckClassifier()
        stuck_type, keywords = classifier.classify(
            "不知道怎么写具体的画面", ""
        )
        assert stuck_type == StuckType.TYPE_2_DETAIL

    def test_classify_transition_stuck(self):
        classifier = StuckClassifier()
        stuck_type, keywords = classifier.classify(
            "两段接不起来", ""
        )
        assert stuck_type == StuckType.TYPE_3_TRANSITION

    def test_classify_emotion_stuck(self):
        classifier = StuckClassifier()
        stuck_type, keywords = classifier.classify(
            "不会写感受", ""
        )
        assert stuck_type == StuckType.TYPE_4_EMOTION

    def test_classify_paragraph_stuck(self):
        classifier = StuckClassifier()
        stuck_type, keywords = classifier.classify(
            "这段写什么", ""
        )
        assert stuck_type == StuckType.TYPE_5_PARAGRAPH

    def test_classify_psychology_stuck(self):
        classifier = StuckClassifier()
        stuck_type, keywords = classifier.classify(
            "不会写内心活动", ""
        )
        assert stuck_type == StuckType.TYPE_6_PSYCHOLOGY

    def test_classify_unknown(self):
        classifier = StuckClassifier()
        stuck_type, keywords = classifier.classify(
            "随便说点什么", ""
        )
        assert stuck_type is None

    def test_detect_ending_keywords(self):
        classifier = StuckClassifier()
        assert classifier._contains_any("帮我看看结尾", classifier.ending_keywords)
        assert classifier._contains_any("不知道怎么收尾", classifier.ending_keywords)
        assert not classifier._contains_any("不知道怎么写开头", classifier.ending_keywords)

    def test_contains_any(self):
        classifier = StuckClassifier()
        assert classifier._contains_any("hello world", ["world"])
        assert not classifier._contains_any("hello world", ["foo"])
