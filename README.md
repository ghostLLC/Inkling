# Inkling — AI 写作卡壳救援助手

面向初中生的记叙文写作过程型辅导系统。**不代写，只引导。**

当学生写到一半卡壳时——不知道怎么开头、情节编不下去、结尾收不住——Inkling 不直接给作文，而是拆解问题、分层引导，帮学生自己找回写作思路。

---

## 核心理念

| 原则 | 说明 |
|------|------|
| **引导优先** | 不给完整作文，只给写作支架 |
| **分层递进** | 根据卡壳严重程度，从方向提示→结构支架→关键词→句式骨架 |
| **交互式审题** | 不是一次性给出题目分析，而是通过对话引导学生自己提炼 |
| **减少依赖** | 同一卡点连续求助 3 次后触发冷却，鼓励学生先独立尝试 |

---

## 快速开始

### 方式1：FastAPI 服务（推荐）

```bash
# 克隆仓库
git clone https://github.com/ghostLLC/Inkling.git
cd Inkling

# 安装依赖
pip install -e ".[dev]"

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key（可选，默认使用 Mock 模式）

# 启动服务
uvicorn app.main:app --reload --port 8080

# 浏览器打开 http://localhost:8080 查看 Demo
# API 文档: http://localhost:8080/docs
```

### 方式2：命令行交互

```bash
python3 demo.py
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `PROVIDER_TYPE` | LLM 提供商: `mock` / `moonshot` / `openai-compatible` | `mock` |
| `LLM_API_KEY` | API Key | - |
| `LLM_BASE_URL` | API 地址 | - |
| `LLM_MODEL` | 模型名称 | - |
| `DATABASE_URL` | 数据库连接 | `sqlite:///./inkling.db` |
| `PORT` | 服务端口 | `8080` |

---

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/health` | 健康检查 |
| `POST` | `/api/sessions` | 创建写作会话 |
| `POST` | `/api/sessions/{id}/messages` | 发送消息，获取 AI 引导 |
| `GET` | `/api/sessions/{id}` | 查询会话状态和对话历史 |

### 快速测试

```bash
# 创建会话
curl -X POST http://localhost:8080/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"topic": "那一刻，我长大了"}'

# 发送消息
curl -X POST http://localhost:8080/api/sessions/xxx/messages \
  -H "Content-Type: application/json" \
  -d '{"session_id": "xxx", "message": "不知道怎么写开头"}'
```

---

## 核心机制

### 1. 审题立意辅助（Topic Analysis）

不是直接给题目分析，而是通过 3-4 轮对话引导学生：
- 题目关键词提取
- 立意方向引导（"你想写什么情感？"）
- 框架确认后进入正文写作

### 2. 卡壳救援分层（Stuck Rescue）

识别 6 种卡壳类型，按层级递进提供引导：

| 层级 | 提供内容 | 目的 |
|------|----------|------|
| **L1 方向** | 情节走向建议 | 不知道写什么 |
| **L2 结构** | 段落功能定位 | 不知道怎么组织 |
| **L3 关键词** | 具体词汇提示 | 表达卡壳 |
| **L4 句式** | 句式骨架参考 | 完全写不出来 |

**冷却机制**：同一卡点连续求助 3 次后，AI 会暂停给提示，鼓励学生先独立写 2-3 句，写完再回来讨论。

### 3. 结尾收束引导（Ending Guide）

检测到"不会结尾"或正文完成后：
- 5 种结尾策略选择（首尾呼应、情感升华、场景定格等）
- 点题方向建议
- 句式支持（不提供完整段落）

### 4. 内容安全边界 v2

三层防护确保不代写：

1. **System Prompt 约束**：模型级行为控制，定义"只引导不代写"
2. **输入检测**：识别"帮我写一篇作文"等代写请求，拒绝并引导
3. **输出拦截**：检测 AI 回复中是否包含可直接提交的完整作文段落，自动截断或降级

---

## 项目结构

```
Inkling/
├── app/                          # FastAPI 分层架构
│   ├── main.py                   # 应用入口（lifespan 管理）
│   ├── api/
│   │   ├── routers/              # HTTP 端点
│   │   │   ├── health.py         # 健康检查
│   │   │   └── sessions.py       # 会话 CRUD + 消息处理
│   │   └── schemas/              # Pydantic 请求/响应模型
│   ├── application/
│   │   ├── handlers/             # 业务逻辑处理器（4 种写作阶段）
│   │   │   ├── topic_analysis.py
│   │   │   ├── stuck_rescue.py
│   │   │   ├── ending_guide.py
│   │   │   └── complete.py
│   │   └── use_cases/            # 用例编排层
│   │       ├── create_session.py
│   │       ├── process_message.py
│   │       └── get_session_info.py
│   ├── domain/
│   │   └── repositories/         # 领域接口（抽象）
│   │       └── session_repository.py
│   └── infrastructure/           # 技术实现层
│       ├── config/               # pydantic-settings 配置
│       │   └── settings.py
│       ├── db/                   # SQLAlchemy + SQLite
│       │   ├── base.py
│       │   └── models.py
│       ├── repositories/         # 仓储实现
│       │   └── sqlalchemy_session_repository.py
│       ├── llm/                  # LLM 提供商适配
│       └── prompts/              # Prompt 模板加载器
│           └── builder.py
├── core/                         # 核心引擎（状态机 + 分类器）
│   ├── state_machine.py          # SessionState / TaskMode / GuideLevel
│   ├── session_manager.py        # 协调层：分发 → Handler → LLM → 安全检查
│   ├── stuck_classifier.py       # 卡壳类型识别 + 意图分类
│   ├── guide_generator.py        # 引导内容生成（委托 PromptBuilder）
│   ├── content_guard.py          # 内容安全过滤（输入检测 + 输出拦截）
│   └── llm_provider.py         # LLM 抽象（Mock / OpenAI Compatible）
├── prompts/                      # 外置 Prompt 模板
│   ├── system_prompt.md          # 系统级约束
│   ├── modes/                    # 4 种写作阶段模板
│   │   ├── topic_analysis.md
│   │   ├── stuck_rescue.md
│   │   ├── ending_guide.md
│   │   └── complete.md
│   ├── levels/                   # L1-L4 分层引导指令
│   │   ├── L1.md ~ L4.md
│   ├── stuck_types/              # 6 种卡壳类型策略
│   │   ├── plot.md ~ psychology.md
│   └── cooldown/                 # 冷却机制指令
│       ├── active.md
│       └── inactive.md
├── static/
│   └── demo.html                 # 前端演示页面
├── tests/
│   ├── test_flows.py             # 18 个核心单元测试
│   ├── integration/              # 13 个集成测试
│   │   ├── test_api.py           # API 端点测试
│   │   └── test_use_cases.py     # 用例层测试
│   └── e2e/                      # 2 个端到端测试
│       └── test_end_to_end.py    # 完整写作流程 + 持久化验证
├── demo.py                       # 命令行交互入口
├── api_server.py                 # 旧版 http.server（保留参考）
├── pyproject.toml
├── .env.example
└── README.md
```

### 架构决策

- **Handler 模式**：`SessionManager` 不直接处理业务逻辑，而是分发到 4 个独立 Handler，每个 Handler 负责一种写作阶段的判断和回复策略
- **Prompt 外置**：所有 prompt 内容提取为 Markdown 模板，运行时通过 `PromptBuilder` 加载和变量替换，改 prompt 无需改代码
- **Repository 模式**：`SessionState` 领域对象与 `SessionORM` 解耦，支持未来切换 PostgreSQL 等生产数据库
- **向后兼容**：`core/` 目录全部保留，18 个原有测试无需修改即可通过

---

## 技术栈

| 层级 | 技术 |
|------|------|
| Web 框架 | FastAPI 0.136 + Uvicorn 0.46 |
| 数据校验 | Pydantic 2.x + pydantic-settings |
| 数据库 | SQLAlchemy 2.0 + SQLite（可升级 PostgreSQL）|
| ORM | 声明式模型 + Repository 模式 |
| LLM | OpenAI SDK 1.x（兼容 Moonshot / DeepSeek / 任何 OpenAI-compatible API）|
| 测试 | pytest + unittest（三层测试：单元 / 集成 / E2E）|
| 代码规范 | ruff（line-length=120, target Python 3.10）|

---

## 测试

```bash
# 运行全部测试（33 个）
python3 -m unittest discover tests -v
python3 -m unittest discover tests/integration -v
python3 -m unittest discover tests/e2e -v

# 单独运行某一层
python3 -m unittest tests/test_flows.py -v           # 18 个单元测试
python3 -m unittest tests/integration/test_api.py -v # 7 个 API 测试
python3 -m unittest tests/integration/test_use_cases.py -v  # 6 个用例测试
python3 -m unittest tests/e2e/test_end_to_end.py -v  # 2 个端到端测试
```

| 测试层 | 数量 | 覆盖范围 |
|--------|------|----------|
| 单元测试 | 18 | 状态机、分类器、内容安全、会话管理 |
| 集成测试 | 13 | API 端点、Use Case 编排 |
| 端到端 | 2 | 完整写作流程、跨请求持久化 |
| **总计** | **33** | |

---

## 开发路线

- [x] 核心引擎：状态机 + 分类器 + 内容安全 v2
- [x] FastAPI 服务化：REST API + SQLite 持久化
- [x] Prompt 模板外置化
- [x] SessionManager 拆分为 Handler 模式
- [x] 三层测试覆盖（18 + 13 + 2 = 33）
- [ ] 卡壳分类器升级（基于语义理解而非关键词）
- [ ] 教师模式（查看学生写作过程、干预引导策略）
- [ ] Docker 容器化 + CI/CD
- [ ] 前端 Demo 升级（React/Vue 交互式写作界面）

---

## License

MIT

---

> 写作不是从空白到完美的跳跃，是从卡壳到继续的循环。Inkling 只负责让你继续。✍️
