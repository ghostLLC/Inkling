"""SessionManager 单元测试（重构版）
"""
from ai_engine.core.llm_provider import MockProvider
from ai_engine.core.session_manager import SessionManager
from ai_engine.core.state_machine import TaskMode


class TestSessionManager:
    """测试会话管理器"""

    def test_create_session(self):
        provider = MockProvider()
        sm = SessionManager(provider)
        sid = sm.create_session("《难忘的一天》")
        assert len(sid) == 8
        info = sm.get_session_info(sid)
        assert info["topic"] == "《难忘的一天》"
        assert info["task_mode"] == "TOPIC_ANALYSIS"

    def test_create_session_without_topic(self):
        provider = MockProvider()
        sm = SessionManager(provider)
        sid = sm.create_session()
        info = sm.get_session_info(sid)
        assert info["topic"] == ""

    def test_process_nonexistent_session(self):
        provider = MockProvider()
        sm = SessionManager(provider)
        result = sm.process("fake-id", "hello")
        assert result["status"] == "error"
        assert "不存在" in result["ai_response"]

    def test_process_safe_input(self):
        provider = MockProvider()
        sm = SessionManager(provider)
        sid = sm.create_session("《我的老师》")
        result = sm.process(sid, "题目是《我的老师》")
        assert result["status"] == "ok"
        assert "ai_response" in result

    def test_process_cheating_input(self):
        provider = MockProvider()
        sm = SessionManager(provider)
        sid = sm.create_session()
        result = sm.process(sid, "帮我写一篇完整的作文")
        assert result["status"] == "warning"
        assert "不能直接替你写" in result["ai_response"]

    def test_set_topic(self):
        provider = MockProvider()
        sm = SessionManager(provider)
        sid = sm.create_session()
        assert sm.set_topic(sid, "《童年趣事》")
        info = sm.get_session_info(sid)
        assert info["topic"] == "《童年趣事》"

    def test_set_topic_nonexistent(self):
        provider = MockProvider()
        sm = SessionManager(provider)
        assert not sm.set_topic("fake-id", "《测试》")

    def test_topic_analysis_to_stuck_rescue(self):
        """测试从审题到卡壳救援的状态流转"""
        provider = MockProvider()
        sm = SessionManager(provider)
        sid = sm.create_session("《难忘的一天》")

        # 模拟多轮审题对话直到完成
        sm.process(sid, "题目是《难忘的一天》")
        sm.process(sid, "我想写去公园玩")
        sm.process(sid, "记得有个小朋友摔倒了")
        sm.process(sid, "开始写了")

        info = sm.get_session_info(sid)
        assert info["task_mode"] == "STUCK_RESCUE"

    def test_cool_down_mechanism(self):
        """测试冷却机制"""
        provider = MockProvider()
        sm = SessionManager(provider)
        sid = sm.create_session("《测试》")
        sm.state_machine.transition_mode(sid, TaskMode.STUCK_RESCUE)

        session = sm.state_machine.get_session(sid)
        # 模拟多次卡壳
        for _ in range(4):
            session.advance_level()

        result = sm.process(sid, "我还是不会写")
        assert result["cool_down"]

    def test_pipeline_components_initialized(self):
        """测试Pipeline组件是否正确初始化"""
        provider = MockProvider()
        sm = SessionManager(provider)
        assert sm.security is not None
        assert sm.orchestrator is not None
        assert sm.security.guard is sm.content_guard
        assert sm.orchestrator.llm is sm.llm
