# Inkling 协作文档

> AI 写作卡壳救援助手 - 多人协作开发指南

## 1. 项目架构

### 1.1 目录结构

```
D:\Inkling\
├── ai_engine/                 # AI 核心引擎（完全独立，不依赖 Web 框架）
│   ├── __init__.py            # 包入口，统一导出
│   ├── core/                  # 核心逻辑
│   │   ├── __init__.py
│   │   ├── state_machine.py   # 状态机：SessionState, TaskMode, GuideLevel, StuckType
│   │   ├── handlers/          # 模式处理器（从 app 解耦到此处）
│   │   │   ├── base.py        # ModeHandler 基类
│   │   │   ├── topic_analysis.py
│   │   │   ├── stuck_rescue.py
│   │   │   ├── ending_guide.py
│   │   │   └── complete.py
│   │   ├── session_manager.py # 会话管理器（协调层）
│   │   ├── guide_generator.py # Prompt 组装器
│   │   ├── stuck_classifier.py# 卡壳类型分类器
│   │   ├── content_guard.py   # 内容安全过滤
│   │   └── llm_provider.py    # LLM 适配器（Mock/Moonshot/OpenAI-compatible）
│   └── prompts/               # 外置 Prompt 模板
│       ├── system_prompt.md
│       ├── modes/             # 各模式 prompt
│       ├── levels/            # L1-L4 层级指令
│       ├── stuck_types/       # 卡壳类型策略
│       └── cooldown/          # 冷却指令
│
├── backend/                   # FastAPI 后端
│   ├── main.py                # 启动入口（python -m backend.main）
│   └── app/
│       ├── main.py            # FastAPI app 定义
│       ├── api/               # API 层
│       │   ├── routers/
│       │   │   ├── health.py  # GET /health
│       │   │   └── sessions.py# POST /api/sessions, POST /api/sessions/{id}/messages
│       │   └── schemas/       # Pydantic 模型
│       ├── application/       # 用例层
│       │   └── use_cases/
│       │       ├── create_session.py
│       │       ├── process_message.py
│       │       └── get_session_info.py
│       ├── domain/            # 领域层
│       │   └── repositories/
│       │       └── session_repository.py  # 仓储接口
│       └── infrastructure/    # 基础设施层
│           ├── config/settings.py     # 配置（pydantic-settings）
│           ├── db/                    # SQLAlchemy ORM
│           ├── prompts/builder.py     # Prompt 模板构建器
│           └── repositories/          # 仓储实现
│
├── frontend/                  # 前端
│   ├── index.html             # 主页面
│   ├── css/style.css          # 样式
│   ├── js/app.js              # 交互逻辑 + API 调用
│   ├── static_legacy/         # 旧版单文件 demo（已废弃）
│   ├── css/                   # （预留）
│   └── js/                    # （预留）
│
├── scripts/                   # 一次性/调试脚本（不参与生产）
│   ├── api_server.py          # 旧版 stdlib HTTP 服务器（legacy）
│   ├── demo.py
│   ├── quickstart.py
│   └── test_*.py
│
├── tests/                     # 测试
│   ├── test_flows.py          # AI 核心单元测试
│   ├── integration/
│   │   ├── test_api.py        # API 端点测试
│   │   └── test_use_cases.py  # 用例层测试
│   └── e2e/
│       └── test_end_to_end.py # 端到端测试
│
├── docs/                      # 文档
├── conftest.py                # pytest 全局配置
├── pyproject.toml             # 项目配置
├── .env.example               # 环境变量模板
└── README.md
```

### 1.2 模块依赖关系

```
frontend ──HTTP──▶ backend/app
                        │
                        ├── uses ──▶ ai_engine（通过 from ai_engine.core import ...）
                        ├── uses ──▶ SQLAlchemy（数据库）
                        └── uses ──▶ pydantic-settings（配置）

ai_engine ◀── 完全独立，不依赖 backend/ 和任何 Web 框架
```

**关键原则**：
- `ai_engine/` **绝不** import `backend/` 或 `app/` 中的任何内容
- `backend/` 可以 import `ai_engine/`，但只通过公开接口（`from ai_engine.core import ...`）
- `frontend/` 只通过 HTTP API 与 `backend/` 通信

---

## 2. API 契约

### 2.1 端点一览

| 方法 | 路径 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/health` | 健康检查 | - | `{ status, app, version, provider_type, has_llm_config }` |
| POST | `/api/sessions` | 创建会话 | `{ topic?: string }` | `{ session_id, status }` |
| POST | `/api/sessions/{id}/messages` | 发送消息 | `{ session_id, message }` | `ChatResponse` |
| GET | `/api/sessions/{id}` | 获取会话信息 | - | `SessionInfoResponse` |

### 2.2 数据模型

```typescript
// ChatResponse
{
  session_id: string
  task_mode: "TOPIC_ANALYSIS" | "STUCK_RESCUE" | "ENDING_GUIDE" | "COMPLETE"
  ai_response: string
  current_level: 1 | 2 | 3 | 4
  stuck_type: string | null      // 如 "情节推进卡"、"细节展开卡"
  cool_down: boolean
  status: "ok" | "warning" | "error"
}

// SessionInfoResponse
{
  session_id: string
  topic: string | null
  task_mode: string
  current_level: number
  stuck_count: number
  cool_down: boolean
  messages: Array<{ role: string, content: string, created_at: string }>
}
```

### 2.3 状态流转

```
TOPIC_ANALYSIS ──"开始写了"──▶ STUCK_RESCUE ──"不会结尾"──▶ ENDING_GUIDE ──"写完了"──▶ COMPLETE
                                  │                              │
                                  └──"还是不会"──▶ 层级递进 L1→L2→L3→L4 ──▶ 冷却
```

---

## 3. 开发规范

### 3.1 环境搭建

```bash
# 克隆项目
cd D:\Inkling

# 安装依赖
pip install -e ".[dev]"

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 LLM API 配置（或使用 mock 模式）

# 启动后端
python -m backend.main
# 或
uvicorn backend.main:app --reload --port 8080
```

### 3.2 Import 规范

| 来源 | 目标 | 正确方式 | 错误方式 |
|------|------|----------|----------|
| ai_engine 内部 | ai_engine 内部 | `from .state_machine import ...` | `from core.state_machine import ...` |
| backend | ai_engine | `from ai_engine.core import ...` | `from core import ...` |
| backend 内部 | backend 内部 | `from app.xxx import ...` | - |

**核心规则**：
- `ai_engine/` 内部全部使用**相对导入**（`from .xxx import`）
- `backend/` 跨模块引用 ai_engine 时使用 `from ai_engine.core import ...`
- `backend/app/` 内部保持 `from app.xxx import ...`

### 3.3 分支规范

```
main                # 生产分支
├── dev             # 开发分支
│   ├── feat/xxx    # 功能分支
│   ├── fix/xxx     # 修复分支
│   └── refactor/xxx
└── release/x.x.x  # 发布分支
```

### 3.4 提交规范

```
feat: 新增 XX 功能
fix: 修复 XX 问题
refactor: 重构 XX 模块
docs: 更新 XX 文档
test: 新增/修改 XX 测试
chore: 构建/配置变更
```

---

## 4. 各模块开发指南

### 4.1 AI 引擎开发（`ai_engine/`）

**负责**：状态机、Handler、Prompt 模板、LLM 适配、安全过滤

**可以独立测试**：
```bash
python -m pytest tests/test_flows.py -v
```

**注意事项**：
- 所有新 Handler 必须继承 `ModeHandler` 基类
- Prompt 模板放在 `ai_engine/prompts/` 下，用 Markdown 格式
- 新增 LLM Provider 必须继承 `LLMProvider` 并在 `create_provider()` 工厂函数中注册
- **不要** import 任何 `app.*` 或 `backend.*` 的模块

**添加新 Handler 的步骤**：
1. 在 `ai_engine/core/handlers/` 下创建新文件
2. 继承 `ModeHandler`，实现 `mode` 属性和 `handle()` 方法
3. 在 `handlers/__init__.py` 中导出
4. 在 `session_manager.py` 的 `_handlers` 字典中注册
5. 在 `state_machine.py` 中添加对应的 `TaskMode` 枚举值
6. 在 `guide_generator.py` 中添加对应的 prompt 生成方法
7. 添加 Prompt 模板到 `ai_engine/prompts/modes/`
8. 编写测试

### 4.2 后端开发（`backend/`）

**负责**：API 路由、用例编排、数据库持久化、配置管理

**架构层次**（严格单向依赖）：
```
api/routers → application/use_cases → domain/repositories
                      ↓                      ↓
                 ai_engine.core     infrastructure/repositories
                                           ↓
                                    infrastructure/db
```

**注意事项**：
- 新增 API 端点在 `api/routers/` 下添加
- 新增用例在 `application/use_cases/` 下添加
- 数据库模型在 `infrastructure/db/models.py`
- 配置项在 `infrastructure/config/settings.py`
- 路由需要注册到 `api/routers/__init__.py` 和 `main.py`

### 4.3 前端开发（`frontend/`）

**负责**：用户界面、交互逻辑、API 调用

**技术栈**：原生 HTML/CSS/JS（暂无构建工具）

**文件组织**：
- `index.html` - 页面结构
- `css/style.css` - 样式
- `js/app.js` - 交互逻辑和 API 调用

**API 调用**：
```javascript
// 创建会话
POST /api/sessions  { topic: "作文题目" }

// 发送消息
POST /api/sessions/{sessionId}/messages  { session_id, message }

// 查询会话
GET /api/sessions/{sessionId}
```

---

## 5. 测试策略

| 层级 | 位置 | 运行命令 | 覆盖内容 |
|------|------|----------|----------|
| AI 核心单元测试 | `tests/test_flows.py` | `pytest tests/test_flows.py -v` | 状态机、分类器、安全、完整流程 |
| 用例层测试 | `tests/integration/test_use_cases.py` | `pytest tests/integration/test_use_cases.py -v` | 创建会话、处理消息、查询会话 |
| API 测试 | `tests/integration/test_api.py` | `pytest tests/integration/test_api.py -v` | HTTP 端点、状态码、响应格式 |
| E2E 测试 | `tests/e2e/test_end_to_end.py` | `pytest tests/e2e/ -v` | 完整写作旅程、持久化验证 |

**运行全部测试**：
```bash
cd D:\Inkling
python -m pytest tests/ -v
```

---

## 6. 配置说明

### 6.1 环境变量（`.env`）

```bash
# 应用
DEBUG=false
PORT=8080

# 数据库
DATABASE_URL=sqlite:///./inkling.db

# LLM 提供商
PROVIDER_TYPE=mock                    # mock / moonshot / openai-compatible
LLM_API_KEY=                          # API Key（mock 模式不需要）
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

### 6.2 LLM 提供商

| 类型 | 说明 | 必要配置 |
|------|------|----------|
| `mock` | 本地模拟，无需 API | 无 |
| `moonshot` | Kimi AI | LLM_API_KEY |
| `openai-compatible` | 任意 OpenAI 兼容 API | LLM_API_KEY, LLM_BASE_URL, LLM_MODEL |

---

## 7. 重构记录（v0.1 → v0.2）

### 解决的问题

1. **core→app 反向依赖**：`core/session_manager.py` 曾 import `app/application/handlers/*`
   - 修复：handlers 移入 `ai_engine/core/handlers/`，session_manager 使用相对导入

2. **双后端并存**：`api_server.py`（stdlib）和 `app/`（FastAPI）暴露不同 API
   - 修复：stdlib 版本移入 `scripts/` 标记为 legacy，统一使用 FastAPI 版本

3. **Prompt 逻辑双份**：`guide_generator.py` 硬编码 + `builder.py` 读模板
   - 当前状态：两者共存，`guide_generator.py` 是主用版本，`builder.py` 是新版（逐步迁移中）

4. **前端单文件**：CSS/JS 全部内联在 HTML 中
   - 修复：拆分为 `index.html` + `css/style.css` + `js/app.js`

5. **API 端点不一致**：旧版 `/api/create_session` + `/api/chat` vs 新版 RESTful 风格
   - 修复：前端 `app.js` 统一使用新版 API 端点

### 目录变更映射

| 旧路径 | 新路径 |
|--------|--------|
| `core/` | `ai_engine/core/` |
| `prompts/` | `ai_engine/prompts/` |
| `app/` | `backend/app/` |
| `app/application/handlers/` | `ai_engine/core/handlers/` |
| `static/demo.html` | `frontend/static_legacy/demo.html` |
| `api_server.py` | `scripts/api_server.py`（legacy） |
| `demo.py`, `quickstart.py`, `test_api.py` | `scripts/`（legacy） |

---

## 8. 常见问题

**Q: 修改了 ai_engine 的代码，后端不生效？**  
A: 确保从项目根目录启动后端（`python -m backend.main`），这样 `sys.path` 包含项目根目录。

**Q: 前端调 API 返回 405？**  
A: 检查 API 端点是否正确。新版使用 RESTful 风格：
- 创建会话：`POST /api/sessions`
- 发消息：`POST /api/sessions/{id}/messages`

**Q: 如何添加新的卡壳类型？**  
A: 1) 在 `state_machine.py` 的 `StuckType` 添加枚举；2) 在 `stuck_classifier.py` 添加关键词；3) 在 `guide_generator.py` 添加 prompt 策略；4) 在 `ai_engine/prompts/stuck_types/` 添加模板。

**Q: 如何切换 LLM 提供商？**  
A: 修改 `.env` 中的 `PROVIDER_TYPE` 和对应配置，重启后端。
