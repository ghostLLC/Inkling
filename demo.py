"""
AI 写作卡壳救援助手 - 可运行的命令行 Demo

使用方法:
    python demo.py

交互说明:
    - 输入作文题目开始审题
    - 输入"开始写了"进入写作阶段
    - 卡住时描述你的问题
    - 输入"不会结尾"进入结尾辅助
    - 输入"写完了"结束本次写作
    - 输入"quit"退出程序
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from core import SessionManager, MockProvider, create_provider


class WritingRescueDemo:
    """命令行交互 Demo"""
    
    def __init__(self):
        print("=" * 50)
        print("📝 AI 写作卡壳救援助手 - Demo 版")
        print("=" * 50)
        print()
        print("我是你的写作陪练，帮你找回思路，不替你写作文。")
        print()
        
        # 初始化 LLM Provider（默认使用模拟器）
        self.provider = self._select_provider()
        self.manager = SessionManager(self.provider)
        self.session_id = None
        self.topic = None
    
    def _select_provider(self):
        """选择 LLM 提供商"""
        # 检查环境变量是否已配置
        import os
        env_key = os.environ.get("OPENAI_API_KEY", "")
        env_url = os.environ.get("OPENAI_BASE_URL", "")
        env_model = os.environ.get("OPENAI_MODEL", "")
        
        has_env_config = bool(env_key and env_url and env_model)
        
        if has_env_config:
            print("🔧 检测到环境变量配置：")
            print(f"   Base URL: {env_url}")
            print(f"   Model: {env_model}")
            print(f"   API Key: {'*' * 20}{env_key[-4:]}")
            print()
            use_env = input("是否使用此配置? [Y/n]: ").strip().lower()
            if use_env in ["", "y", "yes"]:
                try:
                    provider = create_provider("openai-compatible", 
                        api_key=env_key, model=env_model, base_url=env_url)
                    print(f"✅ 已连接: {env_url}")
                    return provider
                except Exception as e:
                    print(f"❌ 连接失败: {e}")
                    print("回退到手动选择...")
                    print()
        
        print("选择 AI 后端：")
        print("1. MockProvider (本地模拟，无需API Key)")
        print("2. Moonshot (Kimi)")
        print("3. OpenAI-Compatible (通用兼容接口)")
        print()
        
        choice = input("输入数字 [1]: ").strip() or "1"
        
        if choice == "2":
            api_key = input("请输入 Moonshot API Key: ").strip()
            if not api_key:
                print("未提供 API Key，回退到 MockProvider")
                return create_provider("mock")
            model = input("模型名称 [kimi-k2p5]: ").strip() or "kimi-k2p5"
            try:
                return create_provider("moonshot", api_key=api_key, model=model)
            except Exception as e:
                print(f"初始化失败: {e}")
                print("回退到 MockProvider")
                return create_provider("mock")
        
        elif choice == "3":
            print()
            print("配置 OpenAI-Compatible 接口：")
            print(f"环境变量 OPENAI_API_KEY: {'已设置' if env_key else '未设置'}")
            print(f"环境变量 OPENAI_BASE_URL: {'已设置' if env_url else '未设置'}")
            print(f"环境变量 OPENAI_MODEL: {'已设置' if env_model else '未设置'}")
            print()
            print("提示：可以通过环境变量配置，或在 .env 文件中设置")
            print()
            
            api_key = env_key or input("API Key: ").strip()
            base_url = env_url or input("Base URL [https://api.openai.com/v1]: ").strip() or "https://api.openai.com/v1"
            model = env_model or input("模型名称 [gpt-4]: ").strip() or "gpt-4"
            
            if not api_key:
                print("未提供 API Key，回退到 MockProvider")
                return create_provider("mock")
            
            try:
                provider = create_provider("openai-compatible", api_key=api_key, model=model, base_url=base_url)
                print(f"✅ 已连接: {base_url}")
                return provider
            except Exception as e:
                print(f"初始化失败: {e}")
                print("回退到 MockProvider")
                return create_provider("mock")
        
        return create_provider("mock")
    
    def run(self):
        """运行主循环"""
        # 第一步：输入作文题目
        print("📌 第一步：输入你的作文题目")
        print("示例：《那一刻，我长大了》")
        print()
        
        topic = input("作文题目: ").strip()
        if not topic:
            topic = "《那一刻，我长大了》"
        
        # 创建会话
        self.session_id = self.manager.create_session(topic=topic)
        self.topic = topic
        
        print()
        print(f"✅ 已创建会话，题目: {topic}")
        print()
        
        # 发送题目给 AI，开始审题
        result = self.manager.process(self.session_id, f"题目是{topic}")
        self._print_ai_response(result)
        
        # 主交互循环
        print()
        print("-" * 50)
        print("💡 提示：输入'开始写了'进入写作阶段")
        print("         输入'quit'退出")
        print("-" * 50)
        print()
        
        while True:
            user_input = input("你: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit", "退出", "结束"]:
                print()
                print("👋 再见。写作有卡壳，随时来找我。")
                break
            
            # 处理用户输入
            result = self.manager.process(self.session_id, user_input)
            self._print_ai_response(result)
            
            # 打印调试信息（可选）
            self._print_debug_info(result)
            print()
    
    def _print_ai_response(self, result):
        """打印 AI 回复"""
        response = result.get("ai_response", "")
        if response:
            print()
            print("🤖:")
            for line in response.split('\n'):
                print(f"   {line}")
            print()
    
    def _print_debug_info(self, result):
        """打印调试信息（开发者视角）"""
        mode = result.get("task_mode", "unknown")
        level = result.get("current_level", 0)
        stuck_type = result.get("stuck_type", "none")
        cool_down = result.get("cool_down", False)
        
        # 只在特定条件下显示调试信息
        if cool_down or level >= 3:
            print(f"   [调试] 模式:{mode} | 层级:L{level} | 卡壳:{stuck_type} | 冷却:{cool_down}")


def run_quick_test():
    """快速测试流程"""
    print("=" * 50)
    print("🧪 快速测试模式")
    print("=" * 50)
    print()
    
    # 使用 MockProvider 进行自动化测试
    provider = create_provider("mock")
    manager = SessionManager(provider)
    
    # 测试 1: 审题立意流程
    print("【测试 1】审题立意流程")
    print("-" * 30)
    
    session_id = manager.create_session(topic="那一刻，我长大了")
    
    test_inputs = [
        "题目是《那一刻，我长大了》",
        "我想写帮妈妈洗碗的事",
        "那个瞬间是我看到妈妈手上的伤口",
        "开始写了"
    ]
    
    for user_input in test_inputs:
        print(f"👤 学生: {user_input}")
        result = manager.process(session_id, user_input)
        print(f"🤖 AI: {result['ai_response'][:100]}...")
        print()
    
    print()
    
    # 测试 2: 卡壳救援流程
    print("【测试 2】卡壳救援流程（情节推进卡）")
    print("-" * 30)
    
    session_id2 = manager.create_session(topic="难忘的一天")
    # 跳过审题，直接进入写作
    session = manager.state_machine.get_session(session_id2)
    session.complete_topic_analysis()
    
    stuck_inputs = [
        "我已经写了开头，写我去参加夏令营，然后不知道怎么继续了",
        "还是不会",
        "还是不懂",
        "还是不会写"
    ]
    
    for user_input in stuck_inputs:
        print(f"👤 学生: {user_input}")
        result = manager.process(session_id2, user_input)
        print(f"🤖 AI: {result['ai_response'][:120]}...")
        print(f"   [状态] 类型:{result['stuck_type']} | 层级:L{result['current_level']} | 冷却:{result['cool_down']}")
        print()
    
    print()
    
    # 测试 3: 结尾收束流程
    print("【测试 3】结尾收束流程")
    print("-" * 30)
    
    session_id3 = manager.create_session(topic="我的老师")
    session3 = manager.state_machine.get_session(session_id3)
    session3.complete_topic_analysis()
    session3.update_written_content("我的老师平时很严格。\n\n但有一次我生病了，她送我去医务室，还帮我倒了热水。\n\n那天我很感动，觉得她其实也很温柔。")
    
    ending_inputs = [
        "正文写完了，不会结尾",
        "我选感悟式"
    ]
    
    for user_input in ending_inputs:
        print(f"👤 学生: {user_input}")
        result = manager.process(session_id3, user_input)
        print(f"🤖 AI: {result['ai_response'][:120]}...")
        print()
    
    print()
    print("=" * 50)
    print("✅ 测试完成")
    print("=" * 50)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AI写作卡壳救援助手 Demo")
    parser.add_argument("--test", action="store_true", help="运行快速测试")
    args = parser.parse_args()
    
    if args.test:
        run_quick_test()
    else:
        demo = WritingRescueDemo()
        demo.run()
