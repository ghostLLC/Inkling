"""Use Case 单元测试"""
import unittest
from unittest.mock import Mock, patch

from core.state_machine import SessionState, TaskMode
from core.llm_provider import MockProvider

from app.application.use_cases.create_session import CreateSessionUseCase
from app.application.use_cases.process_message import ProcessMessageUseCase
from app.application.use_cases.get_session_info import GetSessionInfoUseCase


class TestCreateSessionUseCase(unittest.TestCase):
    """创建会话用例测试"""
    
    def setUp(self):
        self.repo = Mock()
        self.use_case = CreateSessionUseCase(self.repo)
    
    def test_create_session_without_topic(self):
        """无题目创建会话"""
        session_id = self.use_case.execute(None)
        self.assertEqual(len(session_id), 8)
        self.repo.save.assert_called_once()
        saved = self.repo.save.call_args[0][0]
        self.assertIsInstance(saved, SessionState)
        self.assertEqual(saved.topic, "")
    
    def test_create_session_with_topic(self):
        """带题目创建会话"""
        session_id = self.use_case.execute("那一刻，我长大了")
        saved = self.repo.save.call_args[0][0]
        self.assertEqual(saved.topic, "那一刻，我长大了")


class TestGetSessionInfoUseCase(unittest.TestCase):
    """获取会话信息用例测试"""
    
    def setUp(self):
        self.repo = Mock()
        self.use_case = GetSessionInfoUseCase(self.repo)
    
    def test_get_existing_session(self):
        """获取存在的会话"""
        session = SessionState("test123")
        session.topic = "测试题目"
        session.task_mode = TaskMode.STUCK_RESCUE
        session.stuck_count = 2
        self.repo.get_by_id.return_value = session
        self.repo.get_messages.return_value = [
            {"role": "user", "content": "hello"},
        ]
        
        info = self.use_case.execute("test123")
        
        self.assertEqual(info["session_id"], "test123")
        self.assertEqual(info["topic"], "测试题目")
        self.assertEqual(info["task_mode"], "STUCK_RESCUE")
        self.assertEqual(info["stuck_count"], 2)
        self.assertEqual(len(info["messages"]), 1)
    
    def test_get_nonexistent_session(self):
        """获取不存在的会话"""
        self.repo.get_by_id.return_value = None
        info = self.use_case.execute("nope")
        self.assertIsNone(info)


class TestProcessMessageUseCase(unittest.TestCase):
    """处理消息用例测试"""
    
    def setUp(self):
        self.repo = Mock()
        self.llm = MockProvider()
        self.use_case = ProcessMessageUseCase(self.repo, self.llm)
    
    def test_process_existing_session(self):
        """处理已存在会话的消息"""
        session = SessionState("test123")
        session.topic = "测试"
        self.repo.get_by_id.return_value = session
        
        result = self.use_case.execute("test123", "开始写了")
        
        self.assertEqual(result["session_id"], "test123")
        self.assertIn("ai_response", result)
        # 验证保存了消息
        self.assertTrue(self.repo.add_message.called)
    
    def test_process_nonexistent_session(self):
        """处理不存在的会话"""
        self.repo.get_by_id.return_value = None
        
        result = self.use_case.execute("nope", "hello")
        
        self.assertEqual(result["status"], "error")
        self.assertIn("会话不存在", result["ai_response"])


if __name__ == "__main__":
    unittest.main()
