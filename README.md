# AI 写作卡壳救援助手

初中记叙文写作过程型辅导产品。不代替完成，只引导。

## 快速开始

### 方式1：Web 交互 Demo（推荐）

```bash
# 配置 DeepSeek API
export OPENAI_API_KEY="你的API Key"
export OPENAI_BASE_URL="https://api.deepseek.com/v1"
export OPENAI_MODEL="deepseek-chat"

# 启动 API 服务器 + Web Demo
python3 api_server.py

# 打开浏览器访问 http://localhost:8080
```

### 方式2：命令行交互

```bash
python3 demo.py
# 选择选项 3 (OpenAI-Compatible)，自动识别环境变量
```

### 方式3：手动配置

```bash
cp .env.example .env
# 编辑 .env 填入 API 配置
python3 demo.py
```

## 项目结构

```
ai-writing-rescue/
├── api_server.py           # Web API 服务器（启动后访问 localhost:8080）
├── demo.py                 # 命令行交互 Demo
├── test_api.py             # API 连通性测试
├── test_real_api.py        # 端到端真实 API 测试
├── core/                   # 核心引擎
│   ├── state_machine.py    # 状态机（审题→卡壳→结尾→完成）
│   ├── stuck_classifier.py # 卡壳类型分类器（6种类型）
│   ├── guide_generator.py  # Prompt 生成器（4层递进）
│   ├── content_guard.py    # 内容安全 v2（精确检测 + 智能降级）
│   ├── session_manager.py  # 会话管理器
│   └── llm_provider.py     # LLM 接入层（Mock/DeepSeek/OpenAI-Compatible）
├── prompts/
│   └── system_prompt.md    # 系统 Prompt（分层约束 + 冷却机制）
├── static/
│   └── demo.html           # Web 交互界面
├── tests/
│   └── test_flows.py       # 18 个单元测试
└── .env.example            # 配置模板
```

## 核心能力

- **审题立意**：关键词分析 → 追问引导 → 起步框架
- **卡壳救援**：6种类型 × 4层递进（L1方向→L2结构→L3关键词→L4示例）
- **冷却机制**：同一卡点连续3次后建议暂停，鼓励独立写作
- **结尾收束**：5种策略选择 → 点题方向 → 关键词指导
- **内容安全 v2**：精确检测代替完成行为，智能降级 + 自动重生成，不粗暴拦截

## 测试

```bash
# 单元测试
python3 -m unittest tests/test_flows.py -v

# API 连通性测试
python3 test_api.py

# 端到端真实 API 测试
python3 test_real_api.py
```

## 状态流转

```
[学生进入] → TOPIC_ANALYSIS（审题立意）
                ↓
    [学生说"开始写了"] → STUCK_RESCUE（卡壳救援）
                            ↓
        [学生说"不会结尾"] → ENDING_GUIDE（结尾收束）
                                  ↓
                        [学生说"写完了"] → COMPLETE（完成）
```

## LLM 接入

支持三种 Provider：
- `mock` — 本地模拟，无需 API Key，用于测试
- `moonshot` — Moonshot AI (Kimi)
- `openai-compatible` — 任意 OpenAI-compatible API（DeepSeek / 第三方代理等）
