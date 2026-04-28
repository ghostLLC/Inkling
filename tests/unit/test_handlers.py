"""Handlers 单元测试
"""
from ai_engine.core.handlers import (
    CompleteHandler,
    EndingGuideHandler,
    StuckRescueHandler,
    TopicAnalysisHandler,
)
from ai_engine.core.state_machine import GuideLevel, SessionState, TaskMode


class TestTopicAnalysisHandler:
    """测试审题立意处理器"""

    def test_extract_topic(self):
        handler = TopicAnalysisHandler()
        topic = handler._extract_topic("我的题目是《难忘的一天》")
        assert topic == "难忘的一天"

    def test_extract_plain_text(self):
        handler = TopicAnalysisHandler()
        topic = handler._extract_topic("难忘的一天")
        assert topic == "难忘的一天"

    def test_handle_requires_llm(self):
        handler = TopicAnalysisHandler()
        session = SessionState(session_id="t-001")
        result = handler.handle(session, "我想写《我的老师》")
        assert result["requires_llm"]
        assert result["transferred_to"] is None

    def test_handle_completion(self):
        handler = TopicAnalysisHandler()
        session = SessionState(session_id="t-002")
        session.add_message("user", "题目是什么")
        session.add_message("assistant", "你想写什么")
        session.add_message("user", "《难忘的一天》")
        session.add_message("assistant", "好的")

        result = handler.handle(session, "开始写了")
        assert not result["requires_llm"]
        assert result["transferred_to"] == TaskMode.STUCK_RESCUE
        assert "开始写吧" in result["ai_response"]


class TestStuckRescueHandler:
    """测试卡壳救援处理器"""

    def test_handle_stuck(self):
        handler = StuckRescueHandler()
        session = SessionState(session_id="s-001")
        session.task_mode = TaskMode.STUCK_RESCUE
        result = handler.handle(session, "我不知道怎么写了")
        assert result["requires_llm"]

    def test_handle_complete_signal(self):
        handler = StuckRescueHandler()
        session = SessionState(session_id="s-002")
        session.task_mode = TaskMode.STUCK_RESCUE
        result = handler.handle(session, "写完了")
        assert not result["requires_llm"]
        assert result["transferred_to"] == TaskMode.COMPLETE

    def test_handle_complete_with_help_word(self):
        handler = StuckRescueHandler()
        session = SessionState(session_id="s-003")
        session.task_mode = TaskMode.STUCK_RESCUE
        session.has_body = True  # 设置有正文，避免触发"正文没写完"分支
        result = handler.handle(session, "写完了但是不会结尾")
        # "不会"是help word，但有"结尾"会触发ending_request
        # 因为has_body=True，所以会流转到ENDING_GUIDE
        assert result["transferred_to"] == TaskMode.ENDING_GUIDE

    def test_handle_ending_request(self):
        handler = StuckRescueHandler()
        session = SessionState(session_id="s-004")
        session.task_mode = TaskMode.STUCK_RESCUE
        session.has_body = True
        result = handler.handle(session, "帮我看看结尾")
        assert result["transferred_to"] == TaskMode.ENDING_GUIDE

    def test_handle_ending_without_body(self):
        handler = StuckRescueHandler()
        session = SessionState(session_id="s-005")
        session.task_mode = TaskMode.STUCK_RESCUE
        session.has_body = False
        result = handler.handle(session, "帮我看看结尾")
        assert result["transferred_to"] is None
        assert "正文好像还没写完" in result["ai_response"]

    def test_advance_level_signal(self):
        handler = StuckRescueHandler()
        session = SessionState(session_id="s-006")
        session.task_mode = TaskMode.STUCK_RESCUE
        session.current_level = GuideLevel.L1_DIRECTION
        result = handler.handle(session, "还是不会")
        assert session.current_level == GuideLevel.L2_STRUCTURE


class TestEndingGuideHandler:
    """测试结尾收束处理器"""

    def test_handle_requires_llm(self):
        handler = EndingGuideHandler()
        session = SessionState(session_id="e-001")
        session.task_mode = TaskMode.ENDING_GUIDE
        result = handler.handle(session, "怎么收尾比较好")
        assert result["requires_llm"]

    def test_handle_complete(self):
        handler = EndingGuideHandler()
        session = SessionState(session_id="e-002")
        session.task_mode = TaskMode.ENDING_GUIDE
        result = handler.handle(session, "写完了")
        assert not result["requires_llm"]
        assert result["transferred_to"] == TaskMode.COMPLETE

    def test_handle_complete_with_help(self):
        handler = EndingGuideHandler()
        session = SessionState(session_id="e-003")
        session.task_mode = TaskMode.ENDING_GUIDE
        result = handler.handle(session, "写完了但是不知道怎么结尾")
        assert result["requires_llm"]  # 有"怎么"，不是完成信号


class TestCompleteHandler:
    """测试完成处理器"""

    def test_handle(self):
        handler = CompleteHandler()
        session = SessionState(session_id="c-001")
        session.task_mode = TaskMode.COMPLETE
        result = handler.handle(session, "还想写一篇")
        assert not result["requires_llm"]
        assert "已经写完" in result["ai_response"]
        assert result["transferred_to"] is None
