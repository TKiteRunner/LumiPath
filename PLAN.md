# LumiPath 开发计划 (Plan · v3 — Decisions Locked)

> AI 驱动的面试追踪 + OKR 个人规划 + **每日学习笔记（Obsidian 兼容 + Git 版本化）** 系统
> 本文档为 **Step 1–4 统一开发蓝图**。v3 为决策锁定版。

## 📊 总体进度（2026-04-21）

| 阶段 | 状态 | 说明 |
|------|------|------|
| **Step 1** — 文档设计 | ✅ 已完成 | architecture / memory-system / notes-vault-spec / database-schema |
| **Step 2** — 后端骨架 | ✅ 已完成 | 78 文件全部就位；核心逻辑已补全（见第 8 节详细对照表） |
| **Step 3** — 异步 & 中间件 | ✅ 已完成 | Redis/PG/Neo4j 真实 IO；9个Tool；WebSocket；Google OAuth；MCP Server |
| **Step 4** — 前端 + MCP | 🔜 待排期 | Next.js 页面；Milkdown 编辑器；MCP 工具暴露 |

---

---

## ✅ 决策锁定（2026-04-21）

| # | 决策项 | 最终选择 |
|---|-------|--------|
| Q1 | 关系型数据库 | **PostgreSQL 16 + pgvector** |
| Q2 | 图数据库 | **保留 Neo4j 5 Community**（Semantic Memory / GraphRAG） |
| Q3 | 消息队列 | **RabbitMQ + Celery**（替代原 Kafka 方案） |
| Q4 | LLM 接入 | **LiteLLM 统一抽象**（用户可绑定自有 API Key：Anthropic / OpenAI / Qwen / DeepSeek / Gemini 等） |
| Q5 | MCP 客户端 | **Obsidian 插件**为主；系统内置多 LLM Provider 直连对话（用户在设置页填 API Key 即用） |
| Q6 | 登录方式 | **邮箱 + 密码**，并支持 **Google OAuth** |
| Q7 | 部署 | **本地 Docker Compose**（MVP），后期迁移云服务器 |
| Q8 | 国际化 | **中英双语**（i18n，zh-CN / en-US） |
| Q9 | Vault 存储 | **本地挂载 + Git 仓库版本化**，配套 `lumipath` CLI 支持 DevOps 自动同步 |
| Q10 | 前端编辑器 | **Milkdown**（ProseMirror，所见即所得 Markdown） |
| Q11 | 笔记同步方向 | **双向**（Web ↔ 文件 ↔ Obsidian） |
| Q12 | 面试复盘/OKR 季报是否导出为 `.md` | **是**（统一进 vault，形成完整知识库） |

### 交付节奏

- **Step 1 阶段**：**只出文档不写代码**，完成后你审核 → 确认后进 Step 2。
- Step 1 产出位于 [docs/](docs/) 目录：
  - [docs/architecture.md](docs/architecture.md) — 系统架构图 + 请求时序图 + 部署视图
  - [docs/memory-system.md](docs/memory-system.md) — 7 层 Cognitive Memory 规范
  - [docs/notes-vault-spec.md](docs/notes-vault-spec.md) — Markdown Vault 规范 + Git + CLI + Obsidian 互通
  - [docs/database-schema.md](docs/database-schema.md) — 完整 SQL DDL + ER 图 + Neo4j Schema

---

> 🆕 **v2 更新**：新增「每日学习与复盘笔记」模块，采用 **Markdown 文件为源 + DB 索引** 的双轨存储，原生兼容 Obsidian Vault。

---

## 1. 项目定位与核心价值

| 维度 | 说明 |
|------|------|
| 系统名 | **LumiPath** ("照亮求职与成长路径") |
| 核心用户 | 求职者、在职跳槽者、职业规划者、有持续学习习惯的知识工作者 |
| 价值主张 | 把"面试复盘 + OKR 规划 + 每日学习笔记 + 个人知识图谱"四件事用 AI Agent 串成一条增长闭环 |
| 差异点 | ① 7 层 Cognitive Memory + LangGraph Multi-Agent + MCP 暴露<br>② **Markdown-first 的笔记源**：你的数据永远在 `.md` 文件里，系统只是索引+智能层，可随时用 Obsidian 打开 |

---

## 2. 核心业务模块（四大模块）

1. **面试追踪与复盘**：公司 × 轮次 × 题目 × 状态，AI 辅助复盘总结。
2. **OKR 规划**：阶段性 O、KR 拆解、每日打卡。
3. **🆕 每日学习与复盘笔记**：按日期组织的 Markdown 笔记，Obsidian 友好，Agent 可读写。
4. **多用户与 RBAC**：手机/邮箱登录、角色权限、多租户数据隔离。

---

## 3. 总体架构决策（需要你确认的关键选择）

### 3.1 关系型数据库：**PostgreSQL**（而非 MySQL）
- **理由**：`jsonb`、`pgvector`、`LISTEN/NOTIFY`、并发更好。
- **影响**：若强制 MySQL，替换为 MySQL 8 + Milvus/Qdrant。

### 3.2 向量/图数据库：**Neo4j + pgvector 双轨**
- **Neo4j**：Semantic Memory（技能/公司/题目/概念节点、掌握度边）。
- **pgvector**：Episodic/Summary Memory 的向量召回 + **每日笔记的语义检索**。
- **备选**：只用 Neo4j Vector Index（省一套存储）。

### 3.3 Agent 框架：**LangGraph 0.2+ Multi-Agent**，Supervisor 模式

**拓扑**：1 个 Supervisor + 4 个 Specialized Agent（各为独立 subgraph）

| Agent | 职责 | 主要 Tools |
|-------|------|-----------|
| Supervisor | 意图识别、路由、汇总 | — |
| Interview Agent | 面试复盘、题目搜索、状态分析 | `search_questions`, `generate_review`, `analyze_status` |
| OKR Agent | OKR 进度、KR 拆解、日任务生成 | `analyze_okr`, `suggest_tasks`, `generate_report` |
| Notes Agent | 笔记助手、语义检索、周月摘要 | `daily_note_assistant`, `search_notes`, `create_summary` |
| Memory Agent | 多层记忆检索（RRF）、记忆固化 | `retrieve_context`, `consolidate`, `update_graph` |

**Agent 间通信**：LangGraph `Command(goto=agent_name, update={...})` 对象，**无网络协议**，共享 `AgentState` TypedDict。

**每 Agent 独立 API Key**：用户可在设置页为每个 Agent 指定不同 LLM Key（如 Interview Agent 用 Claude Opus，Notes Agent 用 DeepSeek）；未指定时 fallback 到用户默认 Key。数据库表：`agent_llm_assignments`。

**每个 Specialized Agent 内部节点**：`retriever → planner → executor → reflector → memory_writer`

- Tools 可插拔（`@register_tool` 装饰器）
- MCP 暴露每个 Tool 给外部（Claude Desktop / Cursor / Obsidian 插件）

### 3.4 异步架构：**RabbitMQ + Celery**（锁定）
- **RabbitMQ**：Celery 的 broker，承载所有异步任务（Agent 长链路、笔记向量化、邮件、Git 提交等）。
- **Celery**：统一 worker 层，按队列分流（`agent_long`、`embedding`、`notify`、`vault_sync`）。
- **WebSocket 推流**：Agent 阶段性输出通过 Redis Pub/Sub 转发给前端。
- **事件日志**：关键事件（笔记保存、面试复盘生成）写入 PG `events` 表做审计与回放。

### 3.5 认证：**JWT (Access + Refresh) + Redis 黑名单**
- 手机/邮箱抽象 Provider；OAuth2 预留。

### 3.6 RBAC：**User ↔ Role ↔ Permission 三表 + 资源级 Policy Decorator**
- 基础角色：`admin` / `premium_user` / `free_user`
- 资源级：`owner_id` 过滤 + 依赖注入强校验；不上 Casbin（过度工程）

### 3.7 🆕 笔记存储策略：**Markdown 文件为源 + DB 元数据索引**

| 方面 | 方案 |
|------|------|
| 源存储 | 每个用户一个 `vault/` 目录，按 `daily/YYYY-MM-DD.md` 组织 |
| 文件系统 | 本地开发：宿主机挂载；生产：S3 兼容对象存储（MinIO / AWS S3 / 阿里 OSS）|
| 元数据 | PostgreSQL `notes` 表：路径、标题、frontmatter、标签、关联 Interview/OKR、embedding 引用 |
| 向量化 | 笔记保存后 → RabbitMQ → 异步 embedding → 存 pgvector |
| Obsidian 兼容 | ① YAML Frontmatter<br>② `[[wiki-link]]` 内链解析<br>③ `#tag` 标签同步<br>④ 用户可直接把 vault 目录用 Obsidian 打开 |
| 同步方向 | **双向**：Web 端编辑 → 写文件 + 更新 DB；外部改文件 → inotify/polling → 回流 DB |
| 冲突处理 | 以文件 `mtime` + DB `version` 为准，冲突时保留 `.conflict-{ts}.md` 副本 |

---

## 4. 技术栈最终清单

| 层级 | 选型 | 版本 |
|------|------|------|
| 前端 | Next.js (App Router) + TS + Tailwind + shadcn/ui + Framer Motion | Next 14 |
| 前端编辑器 | **Milkdown** 或 **TipTap**（所见即所得 + Markdown 互转） | latest |
| 前端状态 | Zustand + TanStack Query | latest |
| 后端 | FastAPI + Pydantic v2 + SQLAlchemy 2.0 async + Alembic | Py 3.11 |
| Markdown 解析 | `markdown-it-py` + `python-frontmatter` | latest |
| 文件同步 | `watchfiles` (inotify) + S3 boto3 | latest |
| Agent | LangGraph + LangChain Core + LiteLLM | latest |
| MCP | mcp (官方 Python SDK) + stdio/SSE | latest |
| 关系库 | PostgreSQL + pgvector | 16 |
| 图库 | Neo4j | 5 Community |
| 缓存 | Redis | 7 |
| 队列 | RabbitMQ + Celery | latest / 5.3 |
| 部署 | Docker Compose + Nginx | latest |

---

## 5. Monorepo 目录结构

```
LumiPath/
├── PLAN.md
├── README.md
├── docker-compose.yml              ← 一键起全套中间件
├── .env.example
├── docs/
│   ├── architecture.md             ← Step 1 产出
│   ├── memory-system.md            ← Step 1 产出：7层记忆数据流
│   ├── notes-vault-spec.md         ← 🆕 Step 1 产出：Markdown vault 规范
│   └── adr/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/v1/
│   │   │   ├── auth.py
│   │   │   ├── interviews.py
│   │   │   ├── okr.py
│   │   │   ├── notes.py            ← 🆕 笔记 CRUD
│   │   │   └── agent.py
│   │   ├── core/                   ← security / deps / exceptions
│   │   ├── db/                     ← engine / session
│   │   ├── models/                 ← ORM
│   │   ├── schemas/                ← Pydantic DTO
│   │   ├── services/
│   │   │   ├── interview_service.py
│   │   │   ├── okr_service.py
│   │   │   ├── notes_service.py    ← 🆕 Markdown 读写、frontmatter 解析
│   │   │   └── vault_sync.py       ← 🆕 文件 ↔ DB 双向同步
│   │   ├── agents/
│   │   │   ├── graph.py            ← LangGraph 主图
│   │   │   ├── tools/              ← 可插拔 Tool
│   │   │   │   ├── search_questions.py
│   │   │   │   ├── analyze_okr.py
│   │   │   │   ├── generate_review.py
│   │   │   │   └── daily_note_assistant.py  ← 🆕 笔记助手 Tool
│   │   │   ├── memory/             ← 7 层记忆实现
│   │   │   └── mcp_server.py       ← MCP 暴露
│   │   ├── workers/                ← Celery worker (RabbitMQ broker)
│   │   │   ├── embedding_worker.py ← 🆕 笔记 embedding 异步化
│   │   │   └── vault_watcher.py    ← 🆕 监听 vault 文件变更
│   │   └── websocket/
│   ├── migrations/
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── (auth)/
│   │   ├── (dashboard)/
│   │   │   ├── interviews/
│   │   │   ├── okr/
│   │   │   ├── notes/              ← 🆕 每日笔记页面
│   │   │   │   ├── page.tsx        ← 日历 + 笔记列表
│   │   │   │   ├── [date]/         ← 单日详情/编辑
│   │   │   │   └── components/
│   │   │   │       ├── MilkdownEditor.tsx
│   │   │   │       ├── DailyCalendar.tsx
│   │   │   │       └── BacklinksPanel.tsx
│   │   │   └── agent/
│   │   └── api/
│   ├── components/
│   │   ├── ui/
│   │   └── macaron/
│   ├── lib/
│   ├── styles/macaron-theme.css
│   └── package.json
├── vault/                          ← 🆕 本地开发用户笔记目录（挂载进容器）
│   └── {user_id}/
│       ├── daily/
│       │   ├── 2026-04-21.md
│       │   └── 2026-04-22.md
│       ├── interviews/             ← AI 复盘报告导出
│       ├── okr/                    ← OKR 季度总结导出
│       └── templates/
│           └── daily-note.md       ← 日记模板
└── infra/
    ├── nginx/
    └── k8s/
```

---

## 6. 🆕 每日学习笔记：Markdown 文件规范

### 6.1 文件命名 & 组织
```
vault/{user_id}/daily/2026-04-21.md
vault/{user_id}/daily/2026-04-22.md
vault/{user_id}/interviews/字节跳动-二面-2026-03-15.md
vault/{user_id}/okr/2026-Q2-目标总结.md
```

### 6.2 日记模板（Frontmatter + 结构化正文）
```markdown
---
date: 2026-04-21
mood: focused
energy: 8
tags: [算法, 系统设计, Redis]
related_interviews: [uuid-of-bytedance-r2]
related_okr: [uuid-kr-3]
linked_questions: [uuid-q-101, uuid-q-102]
---

# 2026-04-21 学习日志

## 🎯 今日目标
- [x] 刷 2 道动态规划
- [ ] 复习 Redis 持久化机制
- [x] 整理字节二面错题

## 📚 学习内容
### Redis RDB vs AOF
...

## 🧠 复盘
### 做得好的
- ...

### 待改进
- ...

## 🔗 关联
- 面试: [[字节跳动-二面-2026-03-15]]
- OKR: [[2026-Q2-目标总结#KR-3]]

## 💡 明日计划
- ...
```

### 6.3 Agent 交互能力
- **读**：Agent 可检索最近 N 天笔记、按标签查询、语义召回"和 Redis 相关的笔记"。
- **写**：Agent 可根据对话补充今日笔记（经用户确认），自动填充「关联面试/OKR」字段。
- **周/月总结**：Agent 按周扫描笔记 → 生成摘要 → 写入 `vault/{user_id}/weekly/2026-W17.md`。
- **学习轨迹图谱**：笔记中的 `#tag` 自动进 Neo4j 成为 Concept 节点，构建个人知识图谱。

### 6.4 与 Obsidian 的互通
| 场景 | 方案 |
|------|------|
| 用户已有 Obsidian Vault | 指定本地路径挂载为 `vault/{user_id}/`，LumiPath 直接读写 |
| 用户在 LumiPath Web 编辑 | 保存即写文件 → Obsidian 端自动刷新 |
| 用户在 Obsidian 编辑 | `watchfiles` 监听 → 触发 RabbitMQ 消息 → 更新 DB 索引 + 重新 embedding |
| 内链 `[[xxx]]` | 后端解析后建立 `note_links` 表双向链接，前端渲染为可点击跳转 |
| `#tag` | 写入 `note_tags`，驱动侧边栏过滤 |

---

## 7. Step 1 详细交付物

### 7.1 `docs/architecture.md`
- Mermaid C4 Container Diagram
- 请求时序图（"生成面试复盘" + **"保存每日笔记并异步向量化"** 两条链路）
- 组件职责表

### 7.2 `docs/memory-system.md`
- 7 层记忆 × 存储矩阵（见下表）
- Mermaid 数据流图

### 7.3 `docs/notes-vault-spec.md` 🆕
- Vault 目录约定
- Frontmatter 字段规范
- 同步冲突策略
- Obsidian 互通细则

### 7.4 数据库核心表（SQLAlchemy 2.0 + Alembic）

| 表 | 用途 |
|---|---|
| `users` | 用户 |
| `roles` / `permissions` / `user_roles` / `role_permissions` | RBAC |
| `companies` | 公司主数据 |
| `interviews` | 面试场次 |
| `interview_questions` | 题目 |
| `interview_reviews` | 复盘报告 |
| `okr_objectives` | OKR 目标 |
| `okr_key_results` | KR |
| `daily_tasks` | 每日任务 |
| 🆕 `notes` | 笔记元数据（path/title/date/frontmatter_jsonb/word_count/checksum） |
| 🆕 `note_tags` | 标签反向索引 |
| 🆕 `note_links` | 双向链接图 |
| 🆕 `note_embeddings` | pgvector 向量 |
| `agent_sessions` | Agent 会话 |
| `agent_messages` | In-Context 消息流 |
| `memory_long_term` | 职业画像/能力模型 |
| `memory_summaries` | 摘要 + embedding |
| `memory_episodes` | 情景记忆 + embedding |
| `memory_procedures` | Tool 执行日志 |
| `tools_registry` | Tool 元数据 |

### 7.5 7 层记忆矩阵（更新后）

| 记忆类型 | 存储 | 与笔记模块的关系 |
|---------|------|-----------------|
| In-Context | LangGraph State | — |
| Short-term | Redis | 缓存今日打开的笔记 |
| Long-term | PostgreSQL | 从长期高频笔记标签提炼能力模型 |
| Summary | PG + pgvector | **周/月笔记总结自动生成** |
| Episodic | PG + pgvector | 某场面试的完整笔记+对话 |
| Semantic | Neo4j | **笔记 #tag → Concept 节点** |
| Procedural | PG `memory_procedures` | Tool 执行日志 |

---

## 8. Step 2–4 交付速览

### Step 2：Backend & Agent 骨架 ✅ 已完成（2026-04-21）

> 78 个后端文件全部就位，详见 [docs/step2-implementation-plan.md](docs/step2-implementation-plan.md)

| 类别 | 文件 | 状态 |
|------|------|------|
| 脚手架 | `pyproject.toml` / `.env.example` / `alembic.ini` | ✅ 完整 |
| DB 层 | `models/` (11 个) + `migrations/` (9 个) | ✅ 完整 |
| 安全层 | `core/security.py` / `core/deps.py` / `core/rbac.py` | ✅ 完整 |
| API 路由 | `api/v1/` (7 个路由) + `main.py` | ✅ 完整 |
| 服务层 | `auth_service.py` / `interview_service.py` / `okr_service.py` | ✅ 完整 |
| 笔记服务 | `notes_service.py`（文件 IO + frontmatter + **DB upsert/list/get/delete**） | ✅ 已补全 |
| Agent 图 | `agents/graph.py`（LangGraph StateGraph） | ✅ 完整 |
| Supervisor | `agents/nodes/supervisor.py`（**LiteLLM 意图分类 + 关键词降级**） | ✅ 已补全 |
| Agent 节点 | `interview_agent` / `notes_agent` / `okr_agent` / `memory_agent` | ✅ 已补全 |
| 记忆管理 | `agents/memory/manager.py`（**RRF 融合 + 并行召回**） | ✅ 已补全 |
| 记忆子类 | 7 层 `BaseMemory` 子类（Redis/PG/Neo4j IO 为 stub） | ✅ 骨架完整 |
| Tool 注册 | `@register_tool` + 9 个 Tool 类（业务逻辑为 stub） | ✅ 骨架完整 |
| Workers | `celery_app.py` / **`embedding_worker.py`**（切块算法）/ **`vault_watcher.py`**（Git + watchfiles） | ✅ 已补全 |

#### Step 2 待 Step 3 完成的 TODO 项

| 文件 | 待实现 |
|------|--------|
| `core/security.py` | Refresh token Redis 黑名单 |
| `auth_service.py` | Google OAuth code exchange + Redis TTL |
| `agents/memory/short_term.py` | Redis GET/HSET 真实 IO |
| `agents/memory/long_term.py` | PG JSONB merge 真实 IO |
| `agents/memory/summary.py` | pgvector ANN 搜索 |
| `agents/memory/episodic.py` | pgvector ANN 搜索 |
| `agents/memory/semantic.py` | Neo4j Cypher 查询 |
| `agents/tools/*.py` | 9 个 Tool 的真实业务逻辑 |
| `workers/embedding_worker.py` | LiteLLM embedding + pgvector 写入 |
| `agents/mcp_server.py` | MCP stdio/SSE 完整实现 |

---

### Step 3：异步 & 中间件 ✅ 已完成（2026-04-21）

> 32 个文件（7 新建 + 25 修改），详见 [docs/step3-implementation-plan.md](docs/step3-implementation-plan.md)

| 类别 | 文件 / 内容 | 状态 |
|------|------------|------|
| 基础设施 | `db/redis.py`（连接池 + Bloom Filter + TTL 抖动）/ `db/neo4j.py`（async driver）/ `websocket/manager.py`（Pub/Sub 转发） | ✅ |
| Auth & Security | `core/security.py` Refresh token 黑名单 / `auth_service.py` Google OAuth httpx exchange + Redis TTL | ✅ |
| Memory 层 | `short_term.py` Redis HSET/GET / `long_term.py` PG JSONB merge / `summary.py` + `episodic.py` pgvector ANN / `semantic.py` Neo4j Cypher | ✅ |
| 共用 LLM 工具 | `agents/llm.py` LiteLLM embedding + chat completion 统一封装 | ✅ |
| 9 个 Tool | `search_questions`（PG 全文 + pgvector）/ `generate_review`（LiteLLM）/ `analyze_status` / `analyze_okr` / `suggest_tasks` / `generate_report` / `daily_note_assistant` / `search_notes` / `create_summary` | ✅ |
| Workers | `embedding_worker.py` LiteLLM + pgvector bulk upsert / `vault_watcher.py` 文件→DB 完整回流 / `agent_worker.py` LangGraph 驱动 + Pub/Sub 推送 | ✅ |
| WebSocket + Chat | `api/v1/agent.py` `/agent/chat`（Celery 投递）+ `/ws/tasks/{id}`（Redis Pub/Sub）| ✅ |
| MCP Server | `agents/mcp_server.py` stdio + SSE 双模式，暴露全部 TOOL_REGISTRY | ✅ |
| 运维 | `infra/supervisord.conf` + `vault_watcher_main.py` 管理 FastAPI / Celery / vault_watcher 三进程 | ✅ |

### Step 4：前端 + MCP（待开发）

- 马卡龙主题 CSS 变量 + shadcn/ui 组件库
- 面试看板 / OKR 树 / Agent 对话界面
- 🆕 笔记日历页（月视图）+ Milkdown 编辑器 + 反向链接面板
- 🆕 MCP 工具：`list_notes`、`search_notes_semantic`、`create_daily_note`、`get_note_by_date`
- MCP 工具：`list_interviews` / `analyze_okr` / `generate_review`
- i18n（zh-CN / en-US）切换

---

## 9. 非功能性需求对照表

| 需求 | 方案 |
|------|------|
| 高并发数据库锁 | 乐观锁 `version` + 关键事务 `SELECT FOR UPDATE` |
| Redis 击穿 | 分布式锁 + 逻辑过期 |
| Redis 穿透 | 布隆过滤器 + 空值短 TTL |
| Redis 雪崩 | TTL 随机抖动 + 多级缓存 |
| LLM 调用削峰 | RabbitMQ 队列 + 消费者限流 |
| 前端不阻塞 | 立即返回 `task_id` + WebSocket 推进度 |
| Tool 可插拔 | `@register_tool` + 自动发现 |
| 🆕 笔记同步一致性 | 文件 mtime + DB version；冲突保留 `.conflict-{ts}.md` |
| 🆕 笔记批量 embedding | RabbitMQ 队列 + rate limit（避免 LLM API 超限） |

---

## 10. 风险与开放问题（等你裁决）

| # | 问题 | 选项 |
|---|------|------|
| Q1 | PG vs MySQL？ | **默认 PG**（建议）/ MySQL |
| Q2 | Neo4j 是否必须？ | **保留** / 砍掉只用 pgvector |
| Q3 | 队列方案？ | **RabbitMQ + Celery**（已锁定，见决策 Q3） |
| Q4 | LLM 供应商？ | **LiteLLM 统一抽象**（推荐）/ 单一 Claude / OpenAI / Qwen / DeepSeek |
| Q5 | MCP 客户端接入 | Claude Desktop / Cursor / **Obsidian 插件**（契合新模块） |
| Q6 | MVP 登录方式？ | **邮箱 + 密码**（省事）/ 完整手机验证码 |
| Q7 | 部署目标？ | 本地 Docker Compose / 云 K8s |
| Q8 | i18n？ | 先中文 / 中英双语 |
| 🆕 Q9 | Vault 存储介质？ | **本地挂载**（开发）/ S3/MinIO（生产）/ Git 仓库（版本化） |
| 🆕 Q10 | 前端编辑器？ | **Milkdown**（ProseMirror，所见即所得）/ TipTap / 纯 Monaco Markdown |
| 🆕 Q11 | 笔记同步方向？ | **双向**（推荐，契合 Obsidian）/ 单向（只 Web→文件） |
| 🆕 Q12 | 是否把 Interview 复盘、OKR 季度总结也导出为 .md 进 vault？ | **是**（统一知识库） / 否 |

---

## 11. 我需要你确认的事项（Checklist）

- [ ] **决策 3.1–3.7** 全部认可（特别是 3.7 笔记存储策略）
- [ ] **风险 Q1–Q12** 给出选择
- [ ] **第 6 节：每日笔记规范**（Frontmatter 字段 + 模板结构）可接受
- [ ] 目录结构（第 5 节）可接受
- [ ] 交付节奏：**一次完成 Step 1 全部产出后再进 Step 2**
- [ ] 是否需要我 **只出文档不写代码** 走到 Step 1 结束 → 你审核 → 再开工

---

**v2 更新摘要**：新增模块 3，笔记以 `.md` 为源存入用户 `vault/`，DB 只存索引元数据 + 向量引用，Obsidian 可直接打开 vault 目录进行编辑，Agent 能读写笔记并自动生成周/月总结。

**等你 review + 回复 Q1–Q12。收到确认后开始 Step 1 三份文档 + models.py。**
