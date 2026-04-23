# AI 写作卡壳救援助手 - 技术总结

## 交付物

1. **产品深化文档** (`product-deep-dive.md`) —— 三个模块拆成可落地的功能点
2. **技术实现 Demo** (`ai-writing-rescue/`) —— 完整可运行的代码
3. **Web 交互 Demo** (`api_server.py` + `static/demo.html`) —— 浏览器打开即用
4. **18 个单元测试** —— 全部通过

## 核心架构

```
状态机驱动：审题 → 卡壳救援 → 结尾收束 → 完成
           ↓          ↓              ↓
      追问引导    6种类型分类    5种策略选择
                4层递进（L1→L4）
              3次求助后冷却
```

## LLM 接入层

| Provider | 状态 | 说明 |
|----------|------|------|
| Mock | ✅ 稳定 | 本地模拟，无需 API Key |
| DeepSeek | ✅ 稳定 | 真实 API，响应约 0.6s |
| OpenAI-Compatible | ✅ 稳定 | 通用兼容接口 |

## 内容安全 v2

- **精确检测**：只拦截可被直接复制提交的完整作文段落
- **智能降级**：轻微越界 → 自动截断；严重越界 → 自动重生成
- **不粗暴拦截**：不会给用户体验造成中断

## Prompt 分层约束

| 层级 | 约束 | DeepSeek 实测 |
|------|------|--------------|
| L1 方向 | 只给2-3个选项，每条≤15字 | ✅ |
| L2 结构 | 只给结构安排，不给词语 | ✅ |
| L3 关键词 | 只给零散词语（2-4字） | ✅ |
| L4 示例 | 最多1个句式骨架，必须留空 | ✅ |
| 冷却 | 强制停止给新内容 | ✅ |

## 快速启动

```bash
cd ai-writing-rescue

# 配置 API
export OPENAI_API_KEY="sk-2c1948a4ead04550935f22bfdcaed6a3"
export OPENAI_BASE_URL="https://api.deepseek.com/v1"
export OPENAI_MODEL="deepseek-chat"

# 启动 Web Demo
python3 api_server.py
# 打开浏览器访问 http://localhost:8080

# 或命令行
python3 demo.py
```