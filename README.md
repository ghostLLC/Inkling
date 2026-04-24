# Inkling

<div align="center">

**AI 写作卡壳救援助手** · 初中生记叙文过程型辅导

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-33%20passed-brightgreen)]()

</div>

---

Inkling 不是作文生成器，而是一个**写作过程陪伴系统**。当学生写到一半卡壳时——开头没思路、情节编不下去、结尾收不住——它不直接给作文，而是拆解问题、分层引导，帮学生自己找回写作方向。

> 写作不是从空白到完美的跳跃，是从卡壳到继续的循环。

---

## ✨ 核心特性

### 🎯 交互式审题
不是一次性给题目分析，而是通过 3-4 轮对话引导学生自己提炼立意、确认框架，再进入正文写作。

### 🆘 卡壳救援分层（L1 → L4）
识别 6 种卡壳类型，按严重程度递进提供引导：

| 层级 | 提供内容 | 解决什么问题 |
|------|----------|--------------|
| **L1 方向** | 情节走向建议 | 不知道写什么 |
| **L2 结构** | 段落功能定位 | 不知道怎么组织 |
| **L3 关键词** | 具体词汇提示 | 表达卡壳 |
| **L4 句式** | 句式骨架参考 | 完全写不出来 |

### 🧊 冷却机制
同一卡点连续求助 3 次后，AI 暂停给提示，鼓励学生先独立写 2-3 句。写作是先写出来再改对的。

### 🛡️ 内容安全边界 v2
三层防护确保不代写：System Prompt 约束 → 输入代写请求识别 → 输出完整作文段落实时拦截。

---

## 🚀 快速开始

### 方式1：FastAPI 服务（推荐）

```bash
git clone https://github.com/ghostLLC/Inkling.git
cd Inkling
pip install -e ".[dev]"

# 可选：配置 LLM（默认 Mock 模式）
cp .env.example .env
# 编辑 .env 填入 API Key

uvicorn app.main:app --reload --port 8080
```

浏览器打开 http://localhost:8080 体验 Demo，API 文档在 http://localhost:8080/docs。

### 方式2：命令行交互

```bash
python3 demo.py
```

---

## 📡 API

```bash
# 创建写作会话
curl -X POST http://localhost:8080/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"topic": "那一刻，我长大了"}'

# 发送消息获取 AI 引导
curl -X POST http://localhost:8080/api/sessions/{id}/messages \
  -H "Content-Type: application/json" \
  -d '{"session_id": "{id}", "message": "不知道怎么写开头"}'
```

| 端点 | 说明 |
|------|------|
| `GET /health` | 健康检查 |
| `POST /api/sessions` | 创建会话 |
| `POST /api/sessions/{id}/messages` | 发送消息 |
| `GET /api/sessions/{id}` | 查询会话状态与历史 |

---

## 🏗️ 架构

```
Inkling/
├── app/
│   ├── api/routers/           # HTTP 接口层 (FastAPI)
│   ├── application/
│   │   ├── handlers/          # 业务处理器（4 种写作阶段）
│   │   └── use_cases/         # 用例编排
│   ├── domain/repositories/   # 领域接口（抽象）
│   └── infrastructure/
│       ├── config/            # pydantic-settings
│       ├── db/                # SQLAlchemy + SQLite
│       ├── repositories/      # 仓储实现
│       ├── llm/               # LLM 适配
│       └── prompts/           # Prompt 模板加载
├── core/                      # 核心引擎
│   ├── state_machine.py       # 会话状态机
│   ├── session_manager.py     # 协调层（分发 → Handler → LLM）
│   ├── stuck_classifier.py    # 卡壳类型识别
│   ├── guide_generator.py     # 引导生成
│   ├── content_guard.py       # 内容安全
│   └── llm_provider.py        # LLM 抽象
├── prompts/                   # 外置 Prompt 模板
│   ├── modes/                 # 4 种阶段模板
│   ├── levels/                # L1-L4 引导指令
│   ├── stuck_types/           # 6 种卡壳策略
│   └── cooldown/              # 冷却机制指令
├── tests/
│   ├── test_flows.py          # 18 单元测试
│   ├── integration/           # 13 集成测试
│   └── e2e/                   # 2 端到端测试
├── static/demo.html           # 前端演示
├── demo.py                    # CLI 入口
└── pyproject.toml
```

**关键设计决策：**
- **Handler 模式**：`SessionManager` 只负责协调，4 种写作阶段的业务逻辑由独立 Handler 处理
- **Prompt 外置**：所有 prompt 提取为 Markdown 模板，改 prompt 无需改代码
- **Repository 模式**：领域对象与 ORM 解耦，未来可无痛切换 PostgreSQL

---

## 🧪 测试

```bash
# 全部测试（33 个）
python3 -m unittest discover tests -v
python3 -m unittest discover tests/integration -v
python3 -m unittest discover tests/e2e -v
```

| 层级 | 数量 | 覆盖 |
|------|------|------|
| 单元测试 | 18 | 状态机、分类器、内容安全 |
| 集成测试 | 13 | API 端点、Use Case |
| 端到端 | 2 | 完整写作流程、持久化 |

---

## 🛠️ 技术栈

- **Backend**: FastAPI · Uvicorn · Pydantic Settings
- **Database**: SQLAlchemy 2.0 · SQLite（可升级 PostgreSQL）
- **LLM**: OpenAI SDK（兼容 Moonshot / DeepSeek / 任意兼容端点）
- **Testing**: pytest · unittest
- **Linting**: ruff（line-length=120, Python 3.10）

---

## 📋 环境变量

| 变量 | 说明 | 默认 |
|------|------|------|
| `PROVIDER_TYPE` | `mock` / `moonshot` / `openai-compatible` | `mock` |
| `LLM_API_KEY` | API Key | - |
| `LLM_BASE_URL` | API 地址 | - |
| `LLM_MODEL` | 模型名称 | - |
| `DATABASE_URL` | 数据库 | `sqlite:///./inkling.db` |
| `PORT` | 服务端口 | `8080` |

---

## 🗺️ 路线图

- [x] 核心引擎（状态机 + 分类器 + 安全边界）
- [x] FastAPI 服务化 + SQLite 持久化
- [x] Prompt 模板外置化
- [x] SessionManager 拆分为 Handler 模式
- [x] 三层测试覆盖（33 个测试）
- [ ] 分类器升级（语义理解替代关键词匹配）
- [ ] 教师模式（查看学生写作过程、干预引导策略）
- [ ] Docker + CI/CD
- [ ] 前端升级（React/Vue 交互式写作界面）

---

## License

MIT

---

<div align="center">

✍️ Inkling 只负责让你继续写下去。

</div>
