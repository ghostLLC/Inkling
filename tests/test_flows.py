"""
AI 写作卡壳救援助手 - 单元测试

运行方式:
    cd /root/.openclaw/workspace/ai-writing-rescue
    python3 -m unittest tests/test_flows.py -v
"""
import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core import (
    SessionManager, MockProvider, StateMachine, SessionState,
    TaskMode, GuideLevel, StuckType, StuckClassifier, ContentGuard
)


class TestStateMachine(unittest.TestCase):
    """测试状态机"""
    
    def setUp(self):
        self.sm = StateMachine()
        self.session = self.sm.create_session("test001")
    
    def test_create_session(self):
        self.assertEqual(self.session.session_id, "test001")
        self.assertEqual(self.session.task_mode, TaskMode.TOPIC_ANALYSIS)
        self.assertEqual(self.session.current_level, GuideLevel.L1_DIRECTION)
    
    def test_advance_level(self):
        self.session.advance_level()
        self.assertEqual(self.session.current_level, GuideLevel.L2_STRUCTURE)
        self.assertEqual(self.session.stuck_count, 1)
    
    def test_should_cool_down(self):
        self.assertFalse(self.session.should_cool_down())
        self.session.stuck_count = 3
        self.assertTrue(self.session.should_cool_down())
    
    def test_complete_topic_analysis(self):
        self.session.complete_topic_analysis()
        self.assertEqual(self.session.task_mode, TaskMode.STUCK_RESCUE)
        self.assertTrue(self.session.topic_analysis_complete)
    
    def test_transition_mode(self):
        self.sm.transition_mode("test001", TaskMode.ENDING_GUIDE)
        self.assertEqual(self.session.task_mode, TaskMode.ENDING_GUIDE)


class TestStuckClassifier(unittest.TestCase):
    """测试卡壳类型分类器"""
    
    def setUp(self):
        self.classifier = StuckClassifier()
    
    def test_plot_stuck(self):
        stuck_type, conf = self.classifier.classify("不知道怎么继续写了")
        self.assertEqual(stuck_type, StuckType.TYPE_1_PLOT)
        self.assertGreater(conf, 0)
    
    def test_detail_stuck(self):
        stuck_type, conf = self.classifier.classify("不知道怎么描写细节")
        self.assertEqual(stuck_type, StuckType.TYPE_2_DETAIL)
    
    def test_emotion_stuck(self):
        stuck_type, conf = self.classifier.classify("不知道怎么抒情")
        self.assertEqual(stuck_type, StuckType.TYPE_4_EMOTION)
    
    def test_ending_keyword(self):
        stuck_type, conf = self.classifier.classify("不会结尾")
        self.assertIsNone(stuck_type)
        self.assertEqual(conf, -1.0)
    
    def test_unknown_stuck(self):
        stuck_type, conf = self.classifier.classify("今天天气不错")
        self.assertIsNone(stuck_type)


class TestContentGuard(unittest.TestCase):
    """测试内容安全"""
    
    def setUp(self):
        self.guard = ContentGuard()
    
    def test_safe_input(self):
        is_safe, reason = self.guard.check_input("我现在卡住了，不知道怎么写")
        self.assertTrue(is_safe)
        self.assertEqual(reason, "")
    
    def test_cheating_request(self):
        is_safe, reason = self.guard.check_input("帮我写一篇完整的作文")
        self.assertFalse(is_safe)
        self.assertIn("不能直接替你写", reason)
    
    def test_sensitive_content(self):
        is_safe, reason = self.guard.check_input("暴力描写")
        self.assertFalse(is_safe)


class TestSessionManager(unittest.TestCase):
    """测试会话管理器（端到端）"""
    
    def setUp(self):
        self.provider = MockProvider()
        self.manager = SessionManager(self.provider)
    
    def test_topic_analysis_flow(self):
        """测试审题立意完整流程"""
        session_id = self.manager.create_session("那一刻，我长大了")
        
        # 第一轮：输入题目
        result = self.manager.process(session_id, "题目是《那一刻，我长大了》")
        self.assertEqual(result["task_mode"], "TOPIC_ANALYSIS")
        
        # 第二轮：表达想法
        result = self.manager.process(session_id, "我想写帮妈妈洗碗")
        self.assertEqual(result["task_mode"], "TOPIC_ANALYSIS")
        
        # 完成审题
        result = self.manager.process(session_id, "开始写了")
        self.assertEqual(result["task_mode"], "STUCK_RESCUE")
    
    def test_stuck_rescue_flow(self):
        """测试卡壳救援分层递进"""
        session_id = self.manager.create_session("难忘的一天")
        session = self.manager.state_machine.get_session(session_id)
        session.complete_topic_analysis()
        
        # L1: 方向引导
        result = self.manager.process(session_id, "不知道怎么继续了")
        self.assertEqual(result["stuck_type"], "情节推进卡")
        self.assertEqual(result["current_level"], 1)
        self.assertFalse(result["cool_down"])
        
        # L2: 结构提示
        result = self.manager.process(session_id, "还是不会")
        self.assertEqual(result["current_level"], 2)
        
        # L3: 关键词
        result = self.manager.process(session_id, "还是不懂")
        self.assertEqual(result["current_level"], 3)
        
        # L4: 冷却
        result = self.manager.process(session_id, "还是不会写")
        self.assertEqual(result["current_level"], 4)
        self.assertTrue(result["cool_down"])
    
    def test_ending_guide_flow(self):
        """测试结尾收束流程"""
        session_id = self.manager.create_session("我的老师")
        session = self.manager.state_machine.get_session(session_id)
        session.complete_topic_analysis()
        session.update_written_content("第一段\n\n第二段\n\n第三段")
        
        # 进入结尾阶段
        result = self.manager.process(session_id, "正文写完了，不会结尾")
        self.assertEqual(result["task_mode"], "ENDING_GUIDE")
        
        # 选择策略
        result = self.manager.process(session_id, "我选感悟式")
        self.assertEqual(result["task_mode"], "ENDING_GUIDE")
    
    def test_complete_flow(self):
        """测试写作完成"""
        session_id = self.manager.create_session("测试")
        session = self.manager.state_machine.get_session(session_id)
        session.complete_topic_analysis()
        
        result = self.manager.process(session_id, "写完了")
        self.assertEqual(result["task_mode"], "COMPLETE")


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_full_user_journey(self):
        """模拟完整用户旅程"""
        provider = MockProvider()
        manager = SessionManager(provider)
        
        # 1. 开始写作
        sid = manager.create_session("那一刻，我长大了")
        r = manager.process(sid, "题目是《那一刻，我长大了》")
        self.assertEqual(r["task_mode"], "TOPIC_ANALYSIS")
        
        # 2. 审题交互
        r = manager.process(sid, "我想写帮妈妈洗碗")
        self.assertEqual(r["task_mode"], "TOPIC_ANALYSIS")
        
        # 3. 开始写作
        r = manager.process(sid, "开始写了")
        self.assertEqual(r["task_mode"], "STUCK_RESCUE")
        
        # 4. 卡壳求助
        r = manager.process(sid, "写到一半不知道怎么继续了")
        self.assertEqual(r["stuck_type"], "情节推进卡")
        self.assertEqual(r["current_level"], 1)
        
        # 5. 递进求助
        r = manager.process(sid, "还是不会")
        self.assertEqual(r["current_level"], 2)
        
        # 6. 继续写作（模拟写了正文）
        session = manager.state_machine.get_session(sid)
        session.update_written_content("开头\n\n中间\n\n结尾前")
        
        # 7. 进入结尾
        r = manager.process(sid, "不会结尾")
        self.assertEqual(r["task_mode"], "ENDING_GUIDE")
        
        # 8. 选择策略
        r = manager.process(sid, "选感悟式")
        self.assertEqual(r["task_mode"], "ENDING_GUIDE")
        
        # 9. 完成
        r = manager.process(sid, "搞定了")
        self.assertEqual(r["task_mode"], "COMPLETE")


if __name__ == '__main__':
    unittest.main(verbosity=2)
