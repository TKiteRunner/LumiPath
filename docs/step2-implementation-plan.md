# Step 2：Backend & Agent 核心骨架 — 实施计划

> 决策版本：Python 3.12 · LangGraph 0.3+ · Memory 子类留 stub（Step 3 接入真实 IO）
> 生成日期：2026-04-21

---

## 文件树（Step 2 产出，共 ~65 文件）

```
backend/
├── pyproject.toml                   ← 依赖声明 (uv / pip-tools)
├── .env.example                     ← 环境变量模板
├── Dockerfile
├── alembic.ini
├── migrations/
│   ├── env.py
│   └── versions/
│       ├── 001_init_extensions.py   ← pgcrypto / vector / pg_trgm / citext
│       ├── 002_users_rbac.py        ← users / roles / permissions
│       ├── 003_user_secrets.py      ← oauth_accounts / user_llm_keys / usage
│       ├── 004_companies_interviews.py
│       ├── 005_okr.py
│       ├── 006_notes_vault.py       ← vault_configs / notes / tags / links / embeddings
│       ├── 007_agent_memory.py      ← sessions / messages / memory_* / skills_registry
│       ├── 008_events_idempotency.py
│       └── 009_seed.py              ← 初始 roles / permissions
└── app/
    ├── main.py                      ← FastAPI 入口 + lifespan
    ├── config.py                    ← Settings (pydantic-settings)
    ├── db/
    │   ├── __init__.py
    │   ├── engine.py                ← AsyncEngine + sessionmaker
    │   └── session.py               ← get_async_session dependency
    ├── models/                      ← SQLAlchemy 2.0 ORM
    │   ├── __init__.py
    │   ├── base.py                  ← DeclarativeBase + TimestampMixin
    │   ├── user.py                  ← User / OAuthAccount / Role / Permission / UserRole / RolePermission
    │   ├── llm_key.py               ← UserLLMKey / AgentLLMAssignment / UserLLMKeyUsage
    │   ├── interview.py             ← Company / Interview / InterviewQuestion / InterviewReview
    │   ├── okr.py                   ← OKRObjective / OKRKeyResult / DailyTask
    │   ├── note.py                  ← Note / NoteTag / NoteLink / NoteEmbedding
    │   ├── vault.py                 ← VaultConfig / Conflict
    │   ├── agent.py                 ← AgentSession / AgentMessage
    │   ├── memory.py                ← MemoryLongTerm / MemorySummary / MemoryEpisode / MemoryProcedure / SkillsRegistry
    │   └── event.py                 ← Event / TaskIdempotency / AccountDeletionLog
    ├── schemas/                     ← Pydantic v2 DTO
    │   ├── __init__.py
    │   ├── auth.py                  ← LoginRequest / TokenResponse / GoogleCallbackRequest
    │   ├── user.py                  ← UserRead / UserUpdate / LLMKeyCreate / LLMKeyRead
    │   ├── interview.py             ← InterviewCreate / InterviewRead / QuestionCreate
    │   ├── okr.py                   ← ObjectiveCreate / KRCreate / DailyTaskCreate
    │   ├── note.py                  ← NoteCreate / NoteRead / DailyNoteUpsert
    │   └── agent.py                 ← ChatRequest / ChatResponse / TaskStatus
    ├── core/
    │   ├── __init__.py
    │   ├── security.py              ← JWT sign/verify / bcrypt / refresh token 黑名单
    │   ├── deps.py                  ← get_current_user / require_permission DI
    │   ├── exceptions.py            ← 统一异常类体系 + FastAPI exception handler
    │   └── rbac.py                  ← permission_required decorator
    ├── api/
    │   └── v1/
    │       ├── __init__.py
    │       ├── router.py            ← 聚合所有 APIRouter
    │       ├── auth.py              ← POST /auth/login  /auth/refresh  /auth/google  /auth/logout
    │       ├── users.py             ← GET/PATCH /users/me  /users/me/llm-keys CRUD  /users/me/agent-assignments
    │       ├── interviews.py        ← CRUD /interviews  POST /interviews/{id}/review
    │       ├── okr.py               ← CRUD /objectives  /key-results  /daily-tasks
    │       ├── notes.py             ← PUT /notes/daily/{date}  GET /notes  GET /notes/{id}
    │       └── agent.py             ← POST /agent/chat  WS /ws/tasks/{task_id}
    ├── services/
    │   ├── __init__.py
    │   ├── auth_service.py          ← 登录 / 注册 / token 刷新 / Google OAuth
    │   ├── interview_service.py     ← 面试 CRUD + 状态机 转换
    │   ├── okr_service.py           ← OKR CRUD + 进度衍生计算
    │   ├── notes_service.py         ← Markdown 读写 + frontmatter 解析 + wikilink/tag 抽取
    │   └── vault_sync.py            ← 文件 ↔ DB 同步 + GitPython 操作
    ├── agents/
    │   ├── __init__.py
    │   ├── state.py                 ← AgentState TypedDict
    │   ├── graph.py                 ← LangGraph StateGraph 主图（compiled_graph）
    │   ├── nodes/
    │   │   ├── __init__.py
    │   │   ├── supervisor.py        ← 意图识别 + Command(goto=...) 路由
    │   │   ├── interview_agent.py   ← 5节点子图 (retriever→planner→executor→reflector→memory_writer)
    │   │   ├── okr_agent.py
    │   │   ├── notes_agent.py
    │   │   └── memory_agent.py
    │   ├── skills/
    │   │   ├── __init__.py
    │   │   ├── base.py              ← BaseSkill ABC + @register_skill + SKILL_REGISTRY
    │   │   ├── search_questions.py
    │   │   ├── generate_review.py
    │   │   ├── analyze_status.py
    │   │   ├── analyze_okr.py
    │   │   ├── suggest_tasks.py
    │   │   ├── generate_report.py
    │   │   ├── daily_note_assistant.py
    │   │   ├── search_notes.py
    │   │   └── create_summary.py
    │   ├── memory/
    │   │   ├── __init__.py
    │   │   ├── base.py              ← BaseMemory ABC (read/write/search)
    │   │   ├── in_context.py        ← InContextMemory — 读写 AgentState
    │   │   ├── short_term.py        ← ShortTermMemory — Redis stub
    │   │   ├── long_term.py         ← LongTermMemory — PG JSONB stub
    │   │   ├── summary.py           ← SummaryMemory — PG+pgvector stub
    │   │   ├── episodic.py          ← EpisodicMemory — PG+pgvector stub
    │   │   ├── semantic.py          ← SemanticMemory — Neo4j Cypher stub
    │   │   ├── procedural.py        ← ProceduralMemory — PG stub
    │   │   └── manager.py           ← MemoryManager + RRF 融合（接口完整，IO stub）
    │   └── mcp_server.py            ← MCP stdio/SSE 骨架
    └── workers/
        ├── __init__.py
        ├── celery_app.py            ← Celery 4队列（agent_long/embedding/notify/vault_sync）
        ├── embedding_worker.py      ← 笔记分块+embedding 骨架
        └── vault_watcher.py         ← watchfiles + Celery 任务桥骨架
```

---

## 实现阶段

| 阶段 | 内容 | 文件数 |
|------|------|--------|
| 0 · 脚手架 | pyproject.toml / .env.example / config.py | 3 |
| 1 · DB 层 | ORM 模型 + Alembic migrations | 19 |
| 2 · 安全 | security / deps / exceptions / rbac | 4 |
| 3 · API 路由 | 6 路由 + router + main.py | 8 |
| 4 · Services | auth / interview / okr / notes / vault_sync | 5 |
| 5 · Agent & Memory | state / graph / 5节点 / 9 Skills / 7层Memory+Manager | 28 |
| 6 · Workers 骨架 | celery_app / embedding / vault_watcher | 4 |

---

## 关键技术决策（锁定）

### 技术版本
| 技术 | 版本 |
|------|------|
| Python | **3.12** |
| FastAPI | 0.115+ |
| LangGraph | **0.3+** |
| LangChain Core | 0.3+ |
| LiteLLM | latest |
| SQLAlchemy | 2.0 async |
| Alembic | 1.13+ |
| Pydantic | v2 |
| Redis (aioredis) | 2.0+ |
| Neo4j driver | 5.x async |
| Celery | 5.3 |
| RabbitMQ broker | amqp:// |

### AgentState 结构
```python
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    session_id: str
    scratchpad: dict
    retrieved: dict        # MemoryManager.retrieve() 结果
    token_budget: int
    next_agent: str | None # Supervisor 路由决策
    current_agent: str | None
```

### LangGraph 主图拓扑
```
START → supervisor
supervisor → [interview_agent | okr_agent | notes_agent | memory_agent | END]
每个 Agent subgraph 内部:
  retriever → planner → executor → reflector → memory_writer → (return to supervisor)
```
- 使用 `Command(goto="interview", update={...})` 路由
- subgraph 结束后通过 `Command(goto="supervisor", resume=True)` 回归

### `@register_skill` 装饰器
```python
SKILL_REGISTRY: dict[str, type[BaseSkill]] = {}

def register_skill(name: str, version: str = "1.0.0"):
    def decorator(cls: type[BaseSkill]) -> type[BaseSkill]:
        SKILL_REGISTRY[name] = cls
        cls.skill_name = name
        cls.skill_version = version
        return cls
    return decorator
```

### LiteLLM Per-Agent Key 路由
查找优先级：
1. `agent_llm_assignments[user_id, agent_name]` → 取对应 `user_llm_keys.api_key_encrypted`
2. `user_llm_keys[user_id, is_default=True]`
3. 系统环境变量兜底 Key

### Memory 子类（Step 2 为 stub）
所有 6 个外部存储子类实现 `BaseMemory` 接口（`read/write/search`），内部逻辑暂时 `raise NotImplementedError / return {}` 占位，Step 3 接入真实 Redis/PG/Neo4j IO。

### 笔记 Frontmatter 解析
```python
import frontmatter  # python-frontmatter
import re

def parse_note(content: str) -> ParsedNote:
    post = frontmatter.loads(content)
    wikilinks = re.findall(r'\[\[([^\]]+)\]\]', post.content)
    hashtags  = re.findall(r'(?<!\w)#([\w/\u4e00-\u9fff]+)', post.content)
    return ParsedNote(metadata=post.metadata, body=post.content,
                      wikilinks=wikilinks, tags=hashtags)
```

---

## 验证计划

```bash
# 1. 启动中间件
docker compose up -d postgres redis rabbitmq neo4j

# 2. 安装依赖
pip install -e ".[dev]"

# 3. 跑 Alembic 迁移
alembic upgrade head

# 4. 启动 FastAPI
uvicorn app.main:app --reload --port 8000

# 5. 健康检查
curl http://localhost:8000/health

# 6. 验证 LangGraph 图可编译
python -c "from app.agents.graph import compiled_graph; print('OK', compiled_graph.get_graph())"

# 7. 验证 SkillRegistry 自动发现
python -c "from app.agents.skills import SKILL_REGISTRY; print(list(SKILL_REGISTRY.keys()))"

# 8. 单元测试
pytest backend/tests/ -v
```

---

## 相关文档

- [architecture.md](architecture.md) — 系统架构 + 请求时序图
- [memory-system.md](memory-system.md) — 7层 Cognitive Memory 规范
- [notes-vault-spec.md](notes-vault-spec.md) — Markdown Vault 规范
- [database-schema.md](database-schema.md) — 完整 DDL + ER图
- [PLAN.md](../PLAN.md) — 全局开发计划
