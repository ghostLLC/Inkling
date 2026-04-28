"""
ContentGuard 单元测试
"""
import pytest
from ai_engine.core.content_guard import ContentGuard, OutputLimiter


class TestContentGuard:
    """测试内容安全过滤器"""

    def test_check_input_safe(self):
        guard = ContentGuard()
        is_safe, reason = guard.check_input("你好，帮我看看作文")
        assert is_safe
        assert reason == ""

    def test_check_input_cheating(self):
        guard = ContentGuard()
        is_safe, reason = guard.check_input("帮我写一篇完整的作文")
        assert not is_safe
        assert "不能直接替你写" in reason

    def test_check_output_safe(self):
        guard = ContentGuard()
        is_valid, processed, reason = guard.check_output("这是一个安全的回复 💡")
        assert is_valid
        assert processed == "这是一个安全的回复 💡"

    def test_check_output_serious_violation(self):
        guard = ContentGuard()
        # 构建一个可被直接复制提交的完整段落（需满足：>300字、无安全标记、2+模式匹配）
        text = (
            "记得那年夏天，天气非常好，阳光明媚，我和好朋友一起去公园玩。"
            "那是一个阳光明媚的下午，我们在宽阔的草地上奔跑，笑声回荡在整个公园。"
            "那一刻，我感到无比快乐，心中充满了温暖的感觉，真的很开心。"
            "我们一起追逐美丽的蝴蝶，直到夕阳西下，才依依不舍地离开公园。"
            "那天发生的事情让我至今难忘，朋友之间的友谊是那么珍贵，值得珍惜。"
            "每当我回忆起那个夏天，心里总是暖暖的，童年时光总是那么美好。"
            "我希望以后还能有这样美好的日子，和朋友们在一起创造更多回忆。"
            "这段经历教会了我友谊的可贵，让我明白了朋友的重要性。"
            "那些快乐的时光永远留在我的记忆里，成为最美好的回忆。"
            "我永远也不会忘记那个夏天发生的所有事情。"
            "那个公园里有美丽的花朵和高大的树木，风景如画。"
            "我们在那里度过了整整一个下午，玩了很多有趣的游戏。"
        )
        is_valid, processed, reason = guard.check_output(text)
        assert not is_valid
        assert "拦截" in reason

    def test_check_output_safe_with_markers(self):
        guard = ContentGuard()
        # 有安全标记的内容不会触发越界检测
        text = "记得那年夏天 💡 我和朋友一起去公园玩。"
        is_valid, processed, reason = guard.check_output(text)
        assert is_valid

    def test_truncate_risky_content(self):
        guard = ContentGuard()
        # 只有超过250字符且无安全标记的段落才会被截断
        text = "好的，以下是一篇作文。" * 25
        result = guard._truncate_risky_content(text)
        assert "..." in result

    def test_truncate_safe_content(self):
        guard = ContentGuard()
        # 短文本不会被截断
        text = "💡 好的，以下是一篇作文。"
        result = guard._truncate_risky_content(text)
        assert "..." not in result

    def test_sanitize_for_display(self):
        guard = ContentGuard()
        # sanitize_for_display处理markdown表格语法
        text = "| 选项 | 内容 |\n| A | 春天 |\n| B | 夏天 |"
        result = guard.sanitize_for_display(text)
        assert "|" not in result


class TestOutputLimiter:
    """测试输出长度限制器"""

    def test_limit_short_text(self):
        limiter = OutputLimiter()
        text = "这是一段很短的文本。"
        result = limiter.limit_output(text)
        assert result == text

    def test_limit_long_text(self):
        limiter = OutputLimiter()
        text = "这是一段文本。" * 100  # 超过500字符
        result = limiter.limit_output(text)
        assert "..." in result or "精简" in result
        assert len(result) <= 600

    def test_count_example_sentences(self):
        limiter = OutputLimiter()
        text = "示例：春天来了。示例：花儿开了。"
        count = limiter.count_example_sentences(text)
        assert count >= 1
