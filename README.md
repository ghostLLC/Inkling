# AI 写作卡壳救援助手

初中记叙文写作过程型辅导产品。不代写，只引导。

## 快速开始

### 方式1：FastAPI 服务（推荐）

```bash
# 安装依赖
pip install -e ".[dev]"

# 启动服务
uvicorn app.main:app --reload --port 8080

# 打开浏览器访问 http://localhost:8080
# API 文档: http://localhost:8080/docs
```

### 方式2：命令行交互

```bash
python3 demo.py
```

### 环境变量配置

```bash
cp .env.example .env
# 编辑 .env 填入 API 配置
```

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `PROVIDER_TYPE` | LLM 提供商: `mock` / `moonshot` / `openai-compatible` | `mock` |
| `LLM_API_KEY` | API Key | - |
| `LLM_BASE_URL` | API 地址 | - |
| `LLM_MODEL` | 模型名称 | - |
| `DATABASE_URL` | 数据库连接 | `sqlite:///./inkling.db` |

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/api/sessions` | 创建会话 |
| POST | `/api/sessions/{id}/messages` | 发送消息 |
| GET | `/api/sessions/{id}` | 查询会话 |

## 核心机制

- **审题立意辅助**：关键词提取 → 立意引导 → 框架建议
- **卡壳救援分层**：L1方向 → L2结构 → L3关键词 → L4句式骨架
- **冷却机制**：同一卡点连续3次后强制鼓励独立写作
- **结尾收束**：5种策略选择 → 点题方向 → 句式支持
- **内容安全 v2**：精确检测代写行为，智能降级 + 自动重生成，不粗暴拦截

## 项目结构

```
ai-writing-rescue/
├── app/                    # FastAPI 应用
│   ├── main.py             # 应用入口
│   ├── api/                # HTTP 接口层
│   │   └── routers/
│   │       ├── health.py
│   │       └── sessions.py
│   ├── application/        # 用例编排层
│   │   └── use_cases/
│   ├── domain/             # 领域层
│   │   └── repositories/
│   └── infrastructure/     # 基础设施层
│       ├── config/
│       ├── db/
│       ├── repositories/
│       └── llm/
├── core/                   # 核心引擎（保留）
│   ├── state_machine.py
│   ├── session_manager.py
│   ├── stuck_classifier.py
│   ├── guide_generator.py
│   ├── content_guard.py
│   └── llm_provider.py
├── prompts/
│   └── system_prompt.md
├── static/
│   └── demo.html
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── test_flows.py       # 18 个单元测试
├── pyproject.toml
├── .env.example
└── README.md
```

## 技术栈

- FastAPI + Uvicorn
- SQLAlchemy + SQLite（可升级 PostgreSQL）
- Pydantic Settings
- OpenAI SDK（兼容 Moonshot / DeepSeek）

## 测试

```bash
# 旧版核心测试
python3 -m unittest tests/test_flows.py -v
```
