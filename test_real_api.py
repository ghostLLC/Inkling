#!/usr/bin/env python3
"""
真实 API 端到端测试
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import SessionManager, create_provider

# 从环境变量读取配置
API_KEY = os.environ.get("OPENAI_API_KEY", "")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "")
MODEL = os.environ.get("OPENAI_MODEL", "")

if not all([API_KEY, BASE_URL, MODEL]):
    print("❌ 请设置环境变量: OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL")
    sys.exit(1)

print("=" * 50)
print("🧪 真实 API 端到端测试")
print("=" * 50)
print(f"Provider: {BASE_URL}")
print(f"Model: {MODEL}")
print()

# 创建 Provider
provider = create_provider("openai-compatible", 
    api_key=API_KEY, model=MODEL, base_url=BASE_URL)

manager = SessionManager(provider)

# 测试 1: 审题立意
print("【测试 1】审题立意")
print("-" * 30)
sid = manager.create_session("那一刻，我长大了")
result = manager.process(sid, "题目是《那一刻，我长大了》")
print(f"👤 学生: 题目是《那一刻，我长大了》")
print(f"🤖 AI: {result['ai_response'][:120]}...")
print(f"   [状态] 模式:{result['task_mode']}")
print()

# 测试 2: 审题交互
print("【测试 2】审题交互")
print("-" * 30)
result = manager.process(sid, "我想写帮妈妈洗碗，看到她的手很粗糙")
print(f"👤 学生: 我想写帮妈妈洗碗，看到她的手很粗糙")
print(f"🤖 AI: {result['ai_response'][:120]}...")
print()

# 测试 3: 开始写作
print("【测试 3】开始写作")
print("-" * 30)
result = manager.process(sid, "开始写了")
print(f"👤 学生: 开始写了")
print(f"🤖 AI: {result['ai_response']}")
print(f"   [状态] 模式:{result['task_mode']}")
print()

# 测试 4: 卡壳救援 L1
print("【测试 4】卡壳救援 L1")
print("-" * 30)
result = manager.process(sid, "我已经写了开头，写我去洗碗，然后不知道怎么继续了")
print(f"👤 学生: 我已经写了开头，写我去洗碗，然后不知道怎么继续了")
print(f"🤖 AI: {result['ai_response'][:150]}...")
print(f"   [状态] 类型:{result['stuck_type']} | 层级:L{result['current_level']} | 冷却:{result['cool_down']}")
print()

# 测试 5: 卡壳救援 L2
print("【测试 5】卡壳救援 L2")
print("-" * 30)
result = manager.process(sid, "还是不会")
print(f"👤 学生: 还是不会")
print(f"🤖 AI: {result['ai_response'][:150]}...")
print(f"   [状态] 层级:L{result['current_level']} | 冷却:{result['cool_down']}")
print()

print("=" * 50)
print("✅ 真实 API 测试完成")
print("=" * 50)
