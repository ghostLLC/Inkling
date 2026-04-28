# Inkling

<div align="center">

**AI 写作卡壳救援助手** · 初中生记叙文过程型辅导

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-94%20passed-brightgreen)]()

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

### 🔍 卡壳类型智能识别
自动识别学生遇到的写作障碍：
- 情节推进卡 · 细节展开卡 · 过渡衔接卡
- 情感表达卡 · 段落结构卡 · 心理描写卡

### 📊 写作进度可视化
实时追踪学生写作进展：已写字数、段落结构、完成度百分比。

### 💬 情绪感知与鼓励
识别学生写作时的情绪状态（焦虑/烦躁/迷茫），提供针对性心理支持。

### 🏋️ 微写作训练舱
提供专项微练习（景物描写、对话写作、心理刻画、结尾升华），针对薄弱点精准训练。

### 📝 写后过程复盘
作文完成后生成个性化复盘报告：写作过程回顾、卡壳点分析、技巧建议。

### 🧊 冷却机制
同一卡点连续求助 3 次后，AI 暂停给提示，鼓励学生先独立写 2-3 句。写作是先写出来再改对的。

### 🛡️ 内容安全边界 v2
三层防护确保不代写：System Prompt 约束 → 输入代写请求识别 → 输出完整作文段落实时拦截。

---

## 🚀 快速开始

```bash
git clone https://github.com/ghostLLC/Inkling.git
cd Inkling
pip install -e ".[dev]"

# 可选：配置 LLM（默认 Mock 模式可免配置直接运行）
cp .env.example .env
# 编辑 .env 填入 API Key

# 启动服务
python -m backend.main
```

浏览器打开 http://localhost:8080 体验 Demo，API 文档在 http://localhost:8080/docs。

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

### 增强功能 API

| 端点 | 说明 |
|------|------|
| `POST /api/enhanced/stuck-type` | 卡壳类型识别 |
| `POST /api/enhanced/progress` | 写作进度追踪 |
| `POST /api/enhanced/emotion` | 情绪感知 |
| `POST /api/enhanced/training` | 微写作训练 |
| `POST /api/enhanced/review` | 写后复盘 |

---

## 🏗️ 架构

```
Inkling/
├── ai_engine/                 # AI 核心引擎（零 Web 依赖，可独立使用）
│   ├── core/
│   │   ├── state_machine.py   # 会话状态机
│   │   ├── session_manager.py # 协调层（分发 → Handler → Pipeline → LLM）
│   │   ├── stuck_classifier.py# 卡壳类型识别
│   │   ├── guide_generator.py # 引导生成
│   │   ├── content_guard.py   # 内容安全
│   │   ├── llm_provider.py    # LLM 抽象
│   │   ├── content_analyzer.py     # 卡壳类型智能识别
│   │   ├── progress_tracker.py     # 写作进度可视化
│   │   ├── emotion_engine.py       # 情绪感知与鼓励
│   │   ├── training_deck.py        # 微写作训练舱
│   │   ├── review_generator.py     # 写后过程复盘
│   │   ├── pipeline/          # Pipeline 组件
│   │   │   ├── security_pipeline.py  # 安全检查流水线
│   │   │   └── llm_orchestrator.py   # LLM 编排器
│   │   └── handlers/          # 业务处理器（4 种写作阶段）
│   │       ├── base.py
│   │       ├── topic_analysis.py
│   │       ├── stuck_rescue.py
│   │       ├── ending_guide.py
│   │       └── complete.py
│   └── prompts/               # 外置 Prompt 模板
│       ├── modes/
│       ├── levels/
│       ├── stuck_types/
│       └── cooldown/
├── backend/                   # FastAPI Web 层
│   ├── main.py                # 入口（uvicorn 启动点）
│   └── app/
│       ├── main.py            # FastAPI app 工厂
│       ├── api/routers/       # HTTP 接口层
│       │   ├── sessions.py    # 核心会话 API
│       │   ├── enhanced.py    # 增强功能 API
│       │   └── health.py      # 健康检查
│       ├── application/use_cases/
│       ├── domain/repositories/
│       └── infrastructure/
│           ├── config/        # pydantic-settings
│           ├── db/            # SQLAlchemy + SQLite
│           ├── repositories/  # 仓储实现
│           └── prompts/       # Prompt 构建器
├── frontend/                  # 前端（纯静态）
│   ├── index.html             # 主页面（聊天界面）
│   ├── enhanced-demo.html     # 增强功能演示
│   ├── css/style.css
│   └── js/app.js
├── tests/
│   ├── unit/                  # 61 个单元测试
│   ├── integration/           # 集成测试
│   ├── e2e/                   # 端到端测试
│   └── test_flows.py          # 核心流程测试
├── docs/
│   └── COLLABORATION.md       # 协作规范
└── pyproject.toml
```

**关键设计决策：**

- **模块解耦**：`ai_engine/` 零 Web 框架依赖，`backend/` 单向依赖 `ai_engine/`，绝不反向。两个模块可独立演进、独立测试。
- **Handler + Pipeline 模式**：`SessionManager` 只负责协调，业务逻辑下沉到 Handler，安全检查与 LLM 编排提取到 Pipeline。
- **Prompt 外置**：所有 prompt 提取为 Markdown 模板，改 prompt 无需改代码。
- **Repository 模式**：领域对象与 ORM 解耦，未来可无痛切换 PostgreSQL。

---

## 🧪 测试

```bash
# 全部测试
python -m pytest tests/ -v

# 仅单元测试
python -m pytest tests/unit/ -v

# 集成测试
python -m pytest tests/integration/ -v

# 端到端测试
python -m pytest tests/e2e/ -v
```

| 层级 | 数量 | 覆盖 |
|------|------|------|
| 单元测试 | 61 | 状态机、分类器、内容安全、Pipeline、Handler |
| 核心测试 | 24 | 完整流程、状态流转 |
| 集成测试 | 6 | Use Case 编排、API 端点 |
| 端到端 | 2 | 完整写作流程、持久化 |
| **总计** | **93** | **全链路覆盖** |

---

## 🛠️ 技术栈

- **AI Engine**: 独立 Python 包，纯业务逻辑，零框架依赖
- **Backend**: FastAPI · Uvicorn · Pydantic Settings
- **Database**: SQLAlchemy 2.0 · SQLite（可升级 PostgreSQL）
- **LLM**: OpenAI SDK（兼容 Moonshot / DeepSeek / 任意兼容端点）
- **Frontend**: 原生 HTML/CSS/JS（逐步迁移至 React/Vue）
- **Testing**: pytest · unittest · TestClient
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
- [x] SessionManager 拆分为 Handler + Pipeline 模式
- [x] 模块解耦重构（ai_engine / backend / frontend 分离）
- [x] 前端 Demo 重构（HTML + CSS + JS 拆分）
- [x] 五大增强模块（卡壳识别 · 进度可视化 · 情绪感知 · 微写作 · 写后复盘）
- [x] 测试覆盖（61 个新单元测试 + Pipeline 测试）
- [ ] 分类器升级（语义理解替代关键词匹配）
- [ ] 教师模式（查看学生写作过程、干预引导策略）
- [ ] Docker + CI/CD
- [ ] 前端升级（React/Vue 交互式写作界面）

---

## License

MIT

---

<div align="center">

Inkling 只负责让你继续写下去。

</div>
