"""API 层集成测试 - FastAPI endpoint 测试"""
import os
import sys
import tempfile
import unittest

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.infrastructure.config.settings import get_settings, reset_settings
from app.infrastructure.db.base import init_db, reset_engine
from app.main import app
from fastapi.testclient import TestClient


class APITestCase(unittest.TestCase):
    """API 测试基类 - 提供通用客户端初始化"""

    def setUp(self):
        self.client = TestClient(app)


class TestHealthEndpoint(APITestCase):
    """健康检查端点测试"""

    def test_health_check(self):
        """GET /health 应返回 ok"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["app"], "inkling")


class TestSessionEndpoints(APITestCase):
    """会话端点测试"""

    @classmethod
    def setUpClass(cls):
        """使用临时数据库"""
        cls.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.temp_db.close()

        # 覆盖配置
        reset_settings()
        reset_engine()
        settings = get_settings()
        settings.database_url = f"sqlite:///{cls.temp_db.name}"

        # 初始化数据库
        init_db()

    @classmethod
    def tearDownClass(cls):
        """清理临时数据库"""
        os.unlink(cls.temp_db.name)
        reset_settings()

    def test_create_session(self):
        """POST /api/sessions 应创建会话"""
        response = self.client.post(
            "/api/sessions",
            json={"topic": "那一刻，我长大了"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("session_id", data)
        self.assertEqual(data["status"], "created")

    def test_send_message(self):
        """POST /api/sessions/{id}/messages 应返回 AI 回复"""
        # 先创建会话
        create_resp = self.client.post("/api/sessions", json={})
        session_id = create_resp.json()["session_id"]

        # 发送消息
        response = self.client.post(
            f"/api/sessions/{session_id}/messages",
            json={"session_id": session_id, "message": "题目是《那一刻，我长大了》"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("ai_response", data)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["task_mode"], "TOPIC_ANALYSIS")

    def test_get_session(self):
        """GET /api/sessions/{id} 应返回会话信息"""
        # 创建会话并发送消息
        create_resp = self.client.post("/api/sessions", json={"topic": "测试题目"})
        session_id = create_resp.json()["session_id"]

        self.client.post(
            f"/api/sessions/{session_id}/messages",
            json={"session_id": session_id, "message": "开始写了"},
        )

        # 查询会话
        response = self.client.get(f"/api/sessions/{session_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["session_id"], session_id)
        self.assertEqual(data["topic"], "测试题目")
        self.assertIn("messages", data)
        self.assertEqual(len(data["messages"]), 2)  # user + assistant

    def test_get_nonexistent_session(self):
        """GET 不存在的会话应返回 404"""
        response = self.client.get("/api/sessions/nonexistent")
        self.assertEqual(response.status_code, 404)


class TestFullConversationFlow(APITestCase):
    """完整对话流程测试"""

    @classmethod
    def setUpClass(cls):
        """使用临时数据库"""
        cls.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.temp_db.close()

        reset_settings()
        reset_engine()
        settings = get_settings()
        settings.database_url = f"sqlite:///{cls.temp_db.name}"

        init_db()

    @classmethod
    def tearDownClass(cls):
        """清理临时数据库"""
        os.unlink(cls.temp_db.name)
        reset_settings()

    def test_topic_to_stuck_rescue(self):
        """审题 → 卡壳救援 状态流转"""
        # 1. 创建会话
        resp = self.client.post("/api/sessions", json={"topic": "那一刻，我长大了"})
        sid = resp.json()["session_id"]

        # 2. 审题阶段对话（至少4轮）
        messages = [
            "题目是《那一刻，我长大了》",
            "我想写洗碗的事",
            "那时候我觉得洗碗很麻烦",
            "开始写了",  # 完成信号
        ]
        for msg in messages:
            resp = self.client.post(
                f"/api/sessions/{sid}/messages",
                json={"session_id": sid, "message": msg},
            )
            self.assertEqual(resp.status_code, 200)

        # 3. 检查状态流转到 STUCK_RESCUE
        info = self.client.get(f"/api/sessions/{sid}").json()
        self.assertEqual(info["task_mode"], "STUCK_RESCUE")

        # 4. 发送卡壳消息
        resp = self.client.post(
            f"/api/sessions/{sid}/messages",
            json={"session_id": sid, "message": "不知道怎么写下去了"},
        )
        data = resp.json()
        self.assertEqual(data["task_mode"], "STUCK_RESCUE")
        self.assertIn("current_level", data)

    def test_cooldown_activation(self):
        """冷却机制激活测试"""
        # 创建会话并进入卡壳救援
        resp = self.client.post("/api/sessions", json={"topic": "测试"})
        sid = resp.json()["session_id"]

        # 先完成审题
        for msg in ["题目是测试", "知道了", "明白了", "开始写了"]:
            self.client.post(
                f"/api/sessions/{sid}/messages",
                json={"session_id": sid, "message": msg},
            )

        # 连续卡壳4次
        cool_down_triggered = False
        for i in range(4):
            resp = self.client.post(
                f"/api/sessions/{sid}/messages",
                json={"session_id": sid, "message": "还是不会"},
            )
            data = resp.json()
            if data.get("cool_down"):
                cool_down_triggered = True
                # 冷却时应有提示用户自己写的文案
                self.assertIn("自己试着写", data["ai_response"])

        # 验证至少有一次触发了冷却
        self.assertTrue(cool_down_triggered, "连续卡壳应至少触发一次冷却")


if __name__ == "__main__":
    unittest.main()
