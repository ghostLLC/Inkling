#!/usr/bin/env python3
"""
API 连通性测试脚本
用法: python3 test_api.py
"""
import sys
import os

# 配置信息（建议通过环境变量传入，不要硬编码）
API_KEY = os.environ.get("OPENAI_API_KEY", "")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://tmlgb.me/v1")
MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.4")

print("=" * 50)
print("🔌 API 连通性测试")
print("=" * 50)
print()

if not API_KEY:
    print("❌ 未设置 OPENAI_API_KEY 环境变量")
    print()
    print("设置方式:")
    print("  export OPENAI_API_KEY='your-api-key'")
    print("  export OPENAI_BASE_URL='https://tmlgb.me/v1'")
    print("  export OPENAI_MODEL='gpt-5.4'")
    sys.exit(1)

print(f"Base URL: {BASE_URL}")
print(f"Model: {MODEL}")
print(f"API Key: {'*' * 20}{API_KEY[-4:]}")
print()

try:
    from openai import OpenAI
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    
    print("🔄 正在测试 API 连接...")
    print()
    
    # 发送一个简单的测试请求
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "你是一个写作助手。"},
            {"role": "user", "content": "你好，请回复\"API连接成功\"即可。"}
        ],
        temperature=0.1,
        max_tokens=50
    )
    
    content = response.choices[0].message.content
    print(f"✅ API 连接成功！")
    print(f"📨 模型回复: {content.strip()}")
    print()
    print("现在可以运行: python3 demo.py")
    print("选择选项 3 (OpenAI-Compatible) 即可使用此 API。")
    
except ImportError:
    print("❌ 缺少 openai SDK")
    print("请运行: pip install openai")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ API 连接失败: {str(e)}")
    print()
    print("可能的原因:")
    print("  - API Key 不正确")
    print("  - Base URL 不可访问")
    print("  - 模型名称不存在")
    print("  - 网络连接问题")
    sys.exit(1)
