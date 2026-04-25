"""端到端测试 - 验证 API + 持久化 + 业务逻辑 完整链路"""
import unittest
import os
import sys
import tempfile

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi.testclient import TestClient

from app.main import app
from app.infrastructure.config.settings import get_settings, reset_settings
from app.infrastructure.db.base import init_db, reset_engine


class TestEndToEnd(unittest.TestCase):
    """端到端完整流程测试"""
    
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
    
    def setUp(self):
        self.client = TestClient(app)
    
    def test_full_writing_journey(self):
        """完整写作旅程：审题 → 卡壳 → 结尾 → 完成"""
        # === 1. 创建会话 ===
        resp = self.client.post("/api/sessions", json={"topic": "那一刻，我长大了"})
        self.assertEqual(resp.status_code, 200)
        sid = resp.json()["session_id"]
        
        # === 2. 审题阶段（至少4轮后完成）===
        topic_messages = [
            "题目是《那一刻，我长大了》",
            "我想写洗碗的事",
            "那时候我觉得洗碗很麻烦",
            "开始写了",
        ]
        for msg in topic_messages:
            resp = self.client.post(
                f"/api/sessions/{sid}/messages",
                json={"session_id": sid, "message": msg},
            )
            self.assertEqual(resp.status_code, 200)
        
        # 验证流转到 STUCK_RESCUE
        info = self.client.get(f"/api/sessions/{sid}").json()
        self.assertEqual(info["task_mode"], "STUCK_RESCUE")
        self.assertEqual(len(info["messages"]), 8)  # 4 user + 4 assistant
        
        # === 3. 卡壳救援 ===
        stuck_messages = [
            "不知道怎么写下去了",
            "还是不会",
            "还是不懂",
        ]
        for msg in stuck_messages:
            resp = self.client.post(
                f"/api/sessions/{sid}/messages",
                json={"session_id": sid, "message": msg},
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["task_mode"], "STUCK_RESCUE")
        
        # === 4. 模拟写正文并进入结尾 ===
        resp = self.client.post(
            f"/api/sessions/{sid}/messages",
            json={"session_id": sid, "message": "那是一个周末的下午，阳光透过窗户洒在地板上。妈妈正在厨房忙碌，额头上渗出了细密的汗珠。她让我帮忙洗碗，我一开始很不情愿，觉得这是大人的事，跟我没关系。可当我无意间看到她手上那道浅浅的伤疤时，心里突然揪了一下。那是常年做家务留下的痕迹吧？我默默地拿起抹布，把她推开，说：妈，今天我来。她愣了一下，然后笑了。那一刻，我觉得自己好像真的长大了。"},
        )
        self.assertEqual(resp.status_code, 200)
        
        # 进入结尾阶段
        resp = self.client.post(
            f"/api/sessions/{sid}/messages",
            json={"session_id": sid, "message": "不会结尾，帮我看看"},
        )
        self.assertEqual(resp.status_code, 200)
        info = self.client.get(f"/api/sessions/{sid}").json()
        self.assertEqual(info["task_mode"], "ENDING_GUIDE")
        
        # === 5. 完成写作 ===
        resp = self.client.post(
            f"/api/sessions/{sid}/messages",
            json={"session_id": sid, "message": "写完了"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["task_mode"], "COMPLETE")
        self.assertIn("写完了", data["ai_response"])
        
        # === 6. 验证持久化 ===
        info = self.client.get(f"/api/sessions/{sid}").json()
        self.assertEqual(info["task_mode"], "COMPLETE")
        # 应该有大量消息记录
        self.assertGreater(len(info["messages"]), 10)
    
    def test_persistence_across_requests(self):
        """验证数据跨请求持久化"""
        # 创建会话
        resp = self.client.post("/api/sessions", json={"topic": "持久化测试"})
        sid = resp.json()["session_id"]
        
        # 发送消息
        self.client.post(
            f"/api/sessions/{sid}/messages",
            json={"session_id": sid, "message": "测试消息"},
        )
        
        # 新建 client（模拟新连接）
        new_client = TestClient(app)
        
        # 应该能查到之前的数据
        info = new_client.get(f"/api/sessions/{sid}").json()
        self.assertEqual(info["topic"], "持久化测试")
        self.assertEqual(len(info["messages"]), 2)


if __name__ == "__main__":
    unittest.main()
