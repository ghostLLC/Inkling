"""StateMachine 单元测试
"""
from ai_engine.core.state_machine import (
    GuideLevel,
    SessionState,
    StateMachine,
    StuckType,
    TaskMode,
)


class TestSessionState:
    """测试 SessionState 数据模型"""

    def test_default_state(self):
        session = SessionState(session_id="test-001")
        assert session.task_mode == TaskMode.TOPIC_ANALYSIS
        assert session.current_level == GuideLevel.L1_DIRECTION
        assert session.stuck_count == 0
        assert session.topic == ""
        assert session.conversation_history == []

    def test_advance_level(self):
        session = SessionState(session_id="test-002")
        session.advance_level()
        assert session.current_level == GuideLevel.L2_STRUCTURE
        assert session.stuck_count == 1

        session.advance_level()
        assert session.current_level == GuideLevel.L3_KEYWORDS
        assert session.stuck_count == 2

        session.advance_level()
        assert session.current_level == GuideLevel.L4_EXAMPLES
        assert session.stuck_count == 3

        # 已到最高层级，不会再变
        session.advance_level()
        assert session.current_level == GuideLevel.L4_EXAMPLES
        assert session.stuck_count == 4

    def test_should_cool_down(self):
        session = SessionState(session_id="test-003")
        assert not session.should_cool_down()
        for _ in range(3):
            session.advance_level()
        assert session.should_cool_down()

    def test_reset_level(self):
        session = SessionState(session_id="test-004")
        session.advance_level()
        session.current_stuck_type = StuckType.TYPE_1_PLOT
        session.reset_level()
        assert session.current_level == GuideLevel.L1_DIRECTION
        assert session.stuck_count == 0
        assert session.current_stuck_type is None

    def test_complete_topic_analysis(self):
        session = SessionState(session_id="test-005")
        session.complete_topic_analysis()
        assert session.task_mode == TaskMode.STUCK_RESCUE
        assert session.topic_analysis_complete

    def test_start_ending_guide(self):
        session = SessionState(session_id="test-006")
        session.complete_topic_analysis()
        session.start_ending_guide()
        assert session.task_mode == TaskMode.ENDING_GUIDE

    def test_complete_writing(self):
        session = SessionState(session_id="test-007")
        session.complete_writing()
        assert session.task_mode == TaskMode.COMPLETE

    def test_add_message(self):
        session = SessionState(session_id="test-008")
        session.add_message("user", "你好")
        assert len(session.conversation_history) == 1
        assert session.conversation_history[0]["role"] == "user"
        assert session.conversation_history[0]["content"] == "你好"

    def test_update_written_content(self):
        session = SessionState(session_id="test-009")
        session.update_written_content("今天天气很好。我去公园玩。")
        assert session.has_introduction
        assert not session.has_body

        # 使用真实换行符
        session.update_written_content("今天天气很好。\n\n我去公园玩。那里有很多花。\n\n下午回家。")
        assert session.has_body
        assert session.has_ending

    def test_to_dict(self):
        session = SessionState(session_id="test-010", topic="《难忘的一天》")
        d = session.to_dict()
        assert d["session_id"] == "test-010"
        assert d["topic"] == "《难忘的一天》"
        assert d["task_mode"] == "TOPIC_ANALYSIS"


class TestStateMachine:
    """测试 StateMachine 管理器"""

    def test_create_and_get_session(self):
        sm = StateMachine()
        session = sm.create_session("s-001")
        assert isinstance(session, SessionState)
        assert sm.get_session("s-001") is session

    def test_get_nonexistent_session(self):
        sm = StateMachine()
        assert sm.get_session("nonexistent") is None

    def test_delete_session(self):
        sm = StateMachine()
        sm.create_session("s-002")
        sm.delete_session("s-002")
        assert sm.get_session("s-002") is None

    def test_get_active_sessions(self):
        sm = StateMachine()
        sm.create_session("s-003")
        sm.create_session("s-004")
        active = sm.get_active_sessions()
        assert len(active) == 2
        assert "s-003" in active
        assert "s-004" in active

    def test_transition_mode(self):
        sm = StateMachine()
        sm.create_session("s-005")
        assert sm.transition_mode("s-005", TaskMode.STUCK_RESCUE)
        session = sm.get_session("s-005")
        assert session.task_mode == TaskMode.STUCK_RESCUE

    def test_transition_nonexistent(self):
        sm = StateMachine()
        assert not sm.transition_mode("nonexistent", TaskMode.STUCK_RESCUE)

    def test_transition_to_ending_guide(self):
        sm = StateMachine()
        sm.create_session("s-006")
        sm.transition_mode("s-006", TaskMode.ENDING_GUIDE)
        session = sm.get_session("s-006")
        assert session.task_mode == TaskMode.ENDING_GUIDE
