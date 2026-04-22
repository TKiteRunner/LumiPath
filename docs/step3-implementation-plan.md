# Step 3：异步 & 中间件 — 实施计划

> 决策版本：接续 Step 2 骨架；所有 stub → 真实 IO；不改变 API contract
> 生成日期：2026-04-21
> **主文档**：[PLAN.md](../PLAN.md) — 本文档是其 Step 3 节的执行细化，所有决策以 PLAN.md 为准。

---

## 对照 PLAN.md 需求（零遗漏检查）

下表逐条列出 PLAN.md § 8「Step 3」要求项及 § 8「Step 2 待 Step 3 完成的 TODO 项」，确认全部覆盖。

| PLAN.md 要求 | 本计划覆盖位置 |
|-------------|--------------|
| `ShortTermMemory` HSET/GET Redis 真实 IO | Phase 2 · `short_term.py` |
| Refresh token Redis 黑名单 | Phase 1 · `security.py` / `auth_service.py` |
| 布隆过滤器（穿透防护） | Phase 0 · `db/redis.py` — `bloom_add / bloom_check` |
| TTL 抖动（雪崩防护） | Phase 0 · `db/redis.py` — `jitter_ttl()` |
| `SummaryMemory` pgvector ANN 搜索 | Phase 2 · `summary.py` |
| `EpisodicMemory` pgvector ANN 搜索 | Phase 2 · `episodic.py` |
| `SemanticMemory` Neo4j Cypher 查询 + `#tag → Concept` 节点写入 | Phase 2 · `semantic.py` |
| `LongTermMemory` PG JSONB merge 真实 IO | Phase 2 · `long_term.py` |
| 9 个 Tool 真实业务逻辑 | Phase 3 · `agents/tools/*.py`（9 个文件） |
| `process_note_embedding` LiteLLM + pgvector 写入 | Phase 4 · `embedding_worker.py` |
| `sync_vault` Git push（已在 Step 2 完成骨架） | Phase 4 · `vault_watcher.py` 完整回流 |
| WebSocket Manager — Redis Pub/Sub → 前端推流 | Phase 0 · `websocket/manager.py` + Phase 5 · `agent.py` |
| Google OAuth httpx code exchange + upsert `oauth_accounts` | Phase 1 · `auth_service.py` |
| `start_vault_watcher()` 长驻进程 supervisord 配置 | Phase 7 · `infra/supervisord.conf` |
| `agents/mcp_server.py` MCP stdio/SSE 完整实现 | Phase 6 · `mcp_server.py` |

---

## 总览

Step 2 已建立完整骨架（78 个文件），Step 3 目标是将所有 `stub / raise NotImplementedError / TODO Step 3` 替换为真实实现，同时新增 4 个基础设施文件。**不新增业务功能，不改动 API 路由签名。**

| 类别 | 新建 | 修改 | 小计 |
|------|------|------|------|
| 基础设施层（Redis / Neo4j / WS） | 4 | 1 | 5 |
| Auth & Security | 0 | 3 | 3 |
| Memory 层（7 层 → 5 个外部 IO） | 0 | 5 | 5 |
| 9 个 Tool 真实实现 | 0 | 9 | 9 |
| Workers（embedding / vault_watcher）| 0 | 2 | 2 |
| WebSocket + Agent Chat 端点 | 0 | 1 | 1 |
| MCP Server | 0 | 1 | 1 |
| 运维（supervisord） | 1 | 0 | 1 |
| **合计** | **5** | **22** | **27** |

---

## 文件树（Step 3 新增 / 修改）

```
backend/
└── app/
    ├── main.py                          ← MODIFY: Redis + Neo4j lifespan hook
    ├── db/
    │   ├── redis.py                     ← NEW: 连接池 + bloom filter + TTL jitter 工具
    │   └── neo4j.py                     ← NEW: Neo4j async driver 单例 + session 工厂
    ├── websocket/
    │   ├── __init__.py                  ← NEW: 空包初始化
    │   └── manager.py                   ← NEW: WebSocketManager（Redis Pub/Sub 转发）
    ├── core/
    │   ├── security.py                  ← MODIFY: blacklist_refresh_token / is_blacklisted
    │   └── deps.py                      ← MODIFY: get_current_user 加黑名单校验
    ├── services/
    │   └── auth_service.py              ← MODIFY: Redis TTL 写入 + Google OAuth httpx exchange
    ├── agents/
    │   ├── memory/
    │   │   ├── short_term.py            ← MODIFY: Redis HSET/GET/EXPIRE 真实 IO
    │   │   ├── long_term.py             ← MODIFY: PG JSONB merge SELECT+UPDATE
    │   │   ├── summary.py               ← MODIFY: pgvector ANN 搜索（memory_summaries）
    │   │   ├── episodic.py              ← MODIFY: pgvector ANN 搜索（memory_episodes）
    │   │   └── semantic.py              ← MODIFY: Neo4j Cypher MERGE + fulltext 查询
    │   ├── tools/
    │   │   ├── search_questions.py      ← MODIFY: PG tsvector + pgvector 混合检索
    │   │   ├── generate_review.py       ← MODIFY: LiteLLM chat + 写 interview_reviews
    │   │   ├── analyze_status.py        ← MODIFY: PG 聚合查询面试状态
    │   │   ├── analyze_okr.py           ← MODIFY: PG 查 OKR 进度 + 衍生计算
    │   │   ├── suggest_tasks.py         ← MODIFY: OKR 上下文 → LiteLLM → DailyTask 建议
    │   │   ├── generate_report.py       ← MODIFY: OKR + 笔记 → LiteLLM → 季报 md
    │   │   ├── daily_note_assistant.py  ← MODIFY: notes_service 读写 + frontmatter patch
    │   │   ├── search_notes.py          ← MODIFY: PG 全文 + pgvector note_embeddings ANN
    │   │   └── create_summary.py        ← MODIFY: 扫描 N 天笔记 → LiteLLM → 周/月摘要
    │   └── mcp_server.py                ← MODIFY: 完整 stdio / SSE MCP 实现
    ├── api/v1/
    │   └── agent.py                     ← MODIFY: /agent/chat（Celery 投递）+ WS（Pub/Sub）
    └── workers/
        ├── embedding_worker.py          ← MODIFY: LiteLLM embed + pgvector bulk upsert
        └── vault_watcher.py             ← MODIFY: trigger_db_sync_for_file 完整回流实现
infra/
└── supervisord.conf                     ← NEW: vault_watcher 长驻进程配置
```

---

## 实现阶段

| 阶段 | 内容 | 文件数 | 估算工作量 |
|------|------|--------|-----------|
| 0 · 基础设施 | Redis 连接池、Neo4j 驱动、WS Manager、main.py lifespan | 5 | 中 |
| 1 · Auth & Security | Refresh token 黑名单、Google OAuth、黑名单校验 | 3 | 中 |
| 2 · Memory 层 | 5 个外部 IO（Redis/PG/pgvector/Neo4j）| 5 | 中高 |
| 3 · 9 个 Tool | 真实业务逻辑（DB 查询 + LLM 调用）| 9 | 高 |
| 4 · Workers | embedding 向量写入、vault 文件回流 | 2 | 中 |
| 5 · WS + Chat | Agent Chat 端点 + WebSocket Pub/Sub | 1 | 中 |
| 6 · MCP Server | stdio + SSE 完整实现 | 1 | 中 |
| 7 · 运维 | supervisord.conf | 1 | 低 |

---

## 关键技术决策

### Phase 0：基础设施层

#### `app/db/redis.py`

```python
import random
from redis.asyncio import Redis, ConnectionPool
from app.config import settings

_pool: ConnectionPool | None = None

async def init_redis_pool() -> None:
    global _pool
    _pool = ConnectionPool.from_url(settings.redis_url, max_connections=20, decode_responses=True)

async def close_redis_pool() -> None:
    if _pool:
        await _pool.disconnect()

def get_redis() -> Redis:
    return Redis(connection_pool=_pool)

def jitter_ttl(base_seconds: int, pct: float = 0.1) -> int:
    """TTL 随机抖动，防止 Redis 雪崩。"""
    delta = int(base_seconds * pct)
    return base_seconds + random.randint(-delta, delta)

# ── Bloom Filter（防缓存穿透）────────────────────────────────────────────────
BLOOM_KEY = "lumipath:bloom:notes"

async def bloom_add(redis: Redis, value: str) -> None:
    await redis.execute_command("BF.ADD", BLOOM_KEY, value)

async def bloom_check(redis: Redis, value: str) -> bool:
    return bool(await redis.execute_command("BF.EXISTS", BLOOM_KEY, value))
```

> **前提**：Redis 需安装 RedisBloom 模块（docker-compose.yml 中使用 `redis/redis-stack` 镜像已内置）。  
> 若 RedisBloom 不可用，降级为空值短 TTL（`SET key "" EX 60`）。

---

#### `app/db/neo4j.py`

```python
from neo4j import AsyncGraphDatabase, AsyncDriver
from app.config import settings

_driver: AsyncDriver | None = None

async def init_neo4j() -> None:
    global _driver
    _driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    await _driver.verify_connectivity()

async def close_neo4j() -> None:
    if _driver:
        await _driver.close()

def get_neo4j() -> AsyncDriver:
    if _driver is None:
        raise RuntimeError("Neo4j driver not initialized")
    return _driver
```

---

#### `app/websocket/manager.py`

```python
import asyncio, json
from fastapi import WebSocket
from app.db.redis import get_redis

class WebSocketManager:
    """
    维护 task_id → WebSocket 映射，
    后台协程从 Redis Pub/Sub 读消息并转发给对应 WebSocket。
    """
    def __init__(self):
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, task_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections[task_id] = ws
        asyncio.create_task(self._forward(task_id, ws))

    async def _forward(self, task_id: str, ws: WebSocket) -> None:
        redis = get_redis()
        async with redis.pubsub() as ps:
            await ps.subscribe(f"task:{task_id}")
            async for msg in ps.listen():
                if msg["type"] == "message":
                    try:
                        await ws.send_text(msg["data"])
                        data = json.loads(msg["data"])
                        if data.get("stage") in ("done", "error"):
                            break
                    except Exception:
                        break
        self._connections.pop(task_id, None)

    async def publish(self, task_id: str, payload: dict) -> None:
        redis = get_redis()
        await redis.publish(f"task:{task_id}", json.dumps(payload, ensure_ascii=False))

ws_manager = WebSocketManager()
```

---

### Phase 1：Auth & Security

#### `app/core/security.py` 新增函数

```python
# 写入黑名单（logout / refresh 后旧 token 失效）
async def blacklist_refresh_token(jti: str, ttl_seconds: int) -> None:
    redis = get_redis()
    await redis.setex(f"bl:jti:{jti}", jitter_ttl(ttl_seconds), "1")

# 校验是否在黑名单（deps.py 中调用）
async def is_token_blacklisted(jti: str) -> bool:
    redis = get_redis()
    return bool(await redis.exists(f"bl:jti:{jti}"))
```

#### `app/services/auth_service.py` 关键改动

| 函数 | 改动点 |
|------|--------|
| `login()` | `await redis.setex(f"refresh:{jti}", ttl, user_id)` — 存合法 refresh jti |
| `logout()` | 解码 refresh token 取 jti → `blacklist_refresh_token()` |
| `refresh_token()` | 验证 jti 未在黑名单 → 签发新 access token → 旧 jti 加黑名单 |
| `google_oauth_callback()` | httpx POST `https://oauth2.googleapis.com/token` 换 code → 获取 userinfo → upsert `oauth_accounts` → 返回 JWT |

Google OAuth 完整流程：

```python
async def google_oauth_callback(self, code: str, db: AsyncSession) -> dict:
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        token_data = token_resp.json()
        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        userinfo = userinfo_resp.json()

    # upsert User + OAuthAccount
    user = await self._upsert_oauth_user(userinfo, db)
    roles = await self._get_role_names(user.id, db)
    access_token = create_access_token(str(user.id), roles)
    refresh_token, jti = create_refresh_token(str(user.id))
    await redis.setex(f"refresh:{jti}", jitter_ttl(settings.jwt_refresh_expire_days * 86400), str(user.id))
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
```

---

### Phase 2：Memory 层真实 IO

#### ShortTermMemory（Redis）

```python
# key 命名空间: short:{user_id}:{field}
async def read(self, key: str, user_id: str = "", **kwargs) -> Any:
    redis = get_redis()
    raw = await redis.hget(f"short:{user_id}", key)
    return json.loads(raw) if raw else None

async def write(self, data: dict, user_id: str = "", ttl: int = 3600, **kwargs) -> None:
    redis = get_redis()
    pipe = redis.pipeline()
    for k, v in data.items():
        pipe.hset(f"short:{user_id}", k, json.dumps(v, ensure_ascii=False))
    pipe.expire(f"short:{user_id}", jitter_ttl(ttl))
    await pipe.execute()
```

#### LongTermMemory（PG JSONB merge）

```python
# 使用 PostgreSQL JSONB jsonb_strip_nulls + || 合并，避免覆盖
UPDATE memory_long_term
SET profile = profile || :patch,
    updated_at = now()
WHERE user_id = :user_id;
-- 不存在时 INSERT ON CONFLICT DO UPDATE
```

#### SummaryMemory / EpisodicMemory（pgvector ANN）

```python
# 向量化 query → 余弦距离 ANN
async def search(self, query: str, top_k: int = 5, user_id: str = "", **kwargs) -> list[dict]:
    embedding = await _embed(query)           # LiteLLM
    rows = await db.execute(
        text("""
            SELECT id, content, 1 - (embedding <-> :vec::vector) AS score
            FROM memory_summaries
            WHERE user_id = :uid
            ORDER BY embedding <-> :vec::vector
            LIMIT :k
        """),
        {"vec": embedding, "uid": user_id, "k": top_k},
    )
    return [dict(r) for r in rows.mappings()]
```

#### SemanticMemory（Neo4j Cypher）

```python
# 写：将笔记 #tag 更新为 Concept 节点
MERGE (u:User {id: $user_id})
MERGE (c:Concept {name: $tag})
MERGE (u)-[r:KNOWS]->(c)
ON CREATE SET r.count = 1, r.first_seen = datetime()
ON MATCH  SET r.count = r.count + 1, r.last_seen = datetime()

# 读：检索用户已知的 Concept
MATCH (u:User {id: $user_id})-[r:KNOWS]->(c:Concept)
RETURN c.name AS concept, r.count AS freq
ORDER BY r.count DESC LIMIT $top_k

# 搜索：全文（使用 Neo4j fulltext index）
CALL db.index.fulltext.queryNodes("concept_name_idx", $query)
YIELD node, score
RETURN node.name AS concept, score LIMIT $top_k
```

---

### Phase 3：9 个 Tool 真实实现

#### Tool 实现策略

每个 Tool 内通过 DI 获取 DB session 和 Redis，遵循以下模式：

```python
async def execute(self, user_id: str, db: AsyncSession, **kwargs) -> dict:
    # 1. 参数验证（Pydantic 或手动）
    # 2. DB / 外部 IO
    # 3. 可选 LiteLLM 调用
    # 4. 写入结果到 DB（如 interview_reviews）
    # 5. 返回结构化 dict
```

| Tool | 实现要点 |
|------|---------|
| `SearchQuestionsTool` | `SELECT … WHERE to_tsvector('chinese', content) @@ plainto_tsquery(:q)` 全文检索 + pgvector ANN on `note_embeddings`，结果 RRF 融合后返回 top_k |
| `GenerateReviewTool` | 查 `interviews` + `interview_questions` 拼 prompt → `litellm.acompletion()` → INSERT `interview_reviews` → 触发 `sync_vault` task |
| `AnalyzeStatusTool` | PG 聚合：各状态面试数、最近 30 天通过率、热门公司 |
| `AnalyzeOKRTool` | 查 `okr_objectives` + `okr_key_results`，计算加权进度 `progress = Σ(kr.current/kr.target * weight)` |
| `SuggestTasksTool` | OKR 未完成 KR → `litellm.acompletion()` → 建议 3~5 条 `DailyTask`，批量 INSERT |
| `GenerateReportTool` | 查本季度 OKR + 近期笔记摘要 → `litellm.acompletion()` → 生成季报 md → `notes_service.upsert_note()` 写 vault |
| `DailyNoteAssistantTool` | `notes_service.get_or_create_daily_note()` + 根据对话 patch frontmatter 字段（`related_interviews` / `related_okr`） |
| `SearchNotesTool` | PG `notes` 全文检索（`pg_trgm similarity`）+ pgvector ANN on `note_embeddings`，RRF 融合 |
| `CreateSummaryTool` | 读取最近 7/30 天笔记正文 → 拼 prompt → `litellm.acompletion()` → 写 `vault/{user_id}/weekly/` 或 `monthly/` |

---

### Phase 4：Workers 完整化

#### `embedding_worker.py` 完整实现

```python
@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def process_note_embedding(self, note_id: str, content: str, model: str = _DEFAULT_MODEL):
    # 1. 剥离 frontmatter → 切块（已在 Step 2 完成）
    chunks = _split_chunks(_strip_frontmatter(content))

    # 2. LiteLLM batch embedding（每批最多 20 个 chunk，避免超限）
    import litellm, asyncio
    vectors = []
    for batch in _batched(chunks, 20):
        resp = litellm.embedding(model=model, input=batch)
        vectors.extend([item["embedding"] for item in resp.data])

    # 3. pgvector bulk upsert（同步 psycopg2，Celery 不运行在 asyncio 事件循环）
    from sqlalchemy import create_engine, text
    engine = create_engine(settings.database_url_sync)   # 新增 sync URL 配置项
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM note_embeddings WHERE note_id = :nid"), {"nid": note_id})
        conn.execute(
            text("""
                INSERT INTO note_embeddings (note_id, chunk_index, chunk_text, embedding)
                VALUES (:nid, :idx, :txt, :vec::vector)
            """),
            [{"nid": note_id, "idx": i, "txt": chunks[i], "vec": str(vectors[i])} for i in range(len(chunks))],
        )
    return {"status": "ok", "note_id": note_id, "chunk_count": len(chunks)}
```

#### `vault_watcher.py` — `trigger_db_sync_for_file` 完整回流

```python
@celery_app.task
def trigger_db_sync_for_file(user_id: str, file_path: str, event_type: str):
    from pathlib import Path
    from app.services.notes_service import NotesService, parse_note
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    p = Path(file_path)
    if not p.exists() or not p.suffix == ".md":
        return {"status": "skipped"}

    content = p.read_text(encoding="utf-8")
    parsed  = parse_note(content)          # 已在 Step 2 实现

    engine = create_engine(settings.database_url_sync)
    with Session(engine) as db:
        svc = NotesService()
        svc.upsert_from_file_path_sync(
            user_id=user_id,
            file_path=str(p),
            parsed=parsed,
            db=db,
        )

    # 触发重新 embedding
    process_note_embedding.delay(
        note_id=str(p.stem),  # 由 upsert 返回的 note_id
        content=content,
    )
    return {"status": "ok", "file": file_path}
```

---

### Phase 5：WebSocket + Agent Chat

#### `app/api/v1/agent.py` — POST /agent/chat 完整实现

```python
@router.post("/chat", response_model=ChatResponse, status_code=202)
async def chat(body: ChatRequest, current_user: CurrentUser, db: AsyncSession = Depends(get_async_session)):
    # 1. 获取或创建 AgentSession
    session = await _get_or_create_session(body.session_id, current_user.id, db)
    # 2. 生成 task_id + 幂等性写入
    task_id = str(uuid.uuid4())
    await db.execute(insert(TaskIdempotency).values(task_id=task_id, status="queued"))
    await db.commit()
    # 3. 投递 Celery agent_long 队列
    from app.workers.agent_worker import run_agent_graph
    run_agent_graph.apply_async(
        args=[str(current_user.id), str(session.id), task_id, body.message],
        queue="agent_long",
    )
    return ChatResponse(session_id=str(session.id), task_id=task_id, status="queued")
```

> **注**：`run_agent_graph` 是新增的 Celery task（在 `workers/agent_worker.py`），负责驱动 LangGraph compiled_graph，并在每个 Agent 节点完成后 `ws_manager.publish(task_id, {...})` 推送进度到 Redis Pub/Sub。

#### WebSocket 端点

```python
@ws_router.websocket("/tasks/{task_id}")
async def task_progress_ws(task_id: uuid.UUID, websocket: WebSocket):
    await ws_manager.connect(str(task_id), websocket)
    try:
        while True:
            await asyncio.sleep(60)   # keepalive；_forward 协程负责实际转发
    except WebSocketDisconnect:
        pass
```

---

### Phase 6：MCP Server

#### `app/agents/mcp_server.py` 完整实现

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, CallToolResult
from app.agents.tools import TOOL_REGISTRY

server = Server("lumipath-mcp")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name=name,
            description=cls(None).tool_schema["description"],
            inputSchema=cls(None).tool_schema["parameters"],
        )
        for name, cls in TOOL_REGISTRY.items()
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name not in TOOL_REGISTRY:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    tool_instance = TOOL_REGISTRY[name](db=None)   # MCP 模式下 db 通过 arguments 传递 user_id
    result = await tool_instance.execute(**arguments)
    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

### Phase 7：运维（supervisord）

#### `infra/supervisord.conf`

```ini
[supervisord]
nodaemon=true
logfile=/var/log/supervisord.log

[program:fastapi]
command=uvicorn app.main:app --host 0.0.0.0 --port 8000
directory=/app
autostart=true
autorestart=true
stdout_logfile=/var/log/fastapi.log
stderr_logfile=/var/log/fastapi.log

[program:celery-worker]
command=celery -A app.workers.celery_app worker -Q agent_long,embedding,notify,vault_sync --concurrency=4
directory=/app
autostart=true
autorestart=true
stdout_logfile=/var/log/celery.log
stderr_logfile=/var/log/celery.log

[program:vault-watcher]
command=python -m app.workers.vault_watcher_main
directory=/app
autostart=true
autorestart=true
stdout_logfile=/var/log/vault_watcher.log
stderr_logfile=/var/log/vault_watcher.log
```

> `vault_watcher_main.py` 是一个独立启动脚本，遍历所有活跃用户，为每个用户启动 `start_vault_watcher(user_id)` 线程。

---

## 新增配置项（`.env.example`）

```dotenv
# Google OAuth
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback

# 同步 DB URL（Celery worker 用，psycopg2）
DATABASE_URL_SYNC=postgresql://lumipath:secret@postgres:5432/lumipath

# Redis
REDIS_URL=redis://redis:6379/0

# Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=lumipath
```

---

## 非功能性实现清单

| 风险 | 实现方案 | 位置 |
|------|---------|------|
| Redis 击穿 | 分布式锁（`SET NX EX`）+ 逻辑过期 | `db/redis.py` |
| Redis 穿透 | RedisBloom BF.ADD/EXISTS，降级空值短 TTL | `db/redis.py` |
| Redis 雪崩 | `jitter_ttl()` 随机抖动 ±10% | `db/redis.py` |
| LLM 限流 | RabbitMQ `embedding` 队列 + `max_retries=3` + 指数退避 | `embedding_worker.py` |
| Token 安全 | Refresh JTI 写 Redis 黑名单，logout 立即失效 | `security.py` / `auth_service.py` |
| pgvector 索引 | `CREATE INDEX CONCURRENTLY ON note_embeddings USING ivfflat (embedding vector_cosine_ops)` | 新 migration `010_pgvector_idx.py` |
| Neo4j 索引 | `CREATE FULLTEXT INDEX concept_name_idx FOR (n:Concept) ON EACH [n.name]` | `semantic.py` 初始化时确保 |

---

## 验证计划

```bash
# 1. 启动所有中间件
docker compose up -d postgres redis neo4j rabbitmq

# 2. 安装/更新依赖
pip install -e ".[dev]"

# 3. 新 pgvector 索引 migration
alembic revision --autogenerate -m "add_pgvector_ivfflat_index"
alembic upgrade head

# 4. 启动 FastAPI（带 Redis + Neo4j lifespan）
uvicorn app.main:app --reload --port 8000

# 5. Auth 流程测试
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Secret123","display_name":"Test"}'
# → 拿到 access_token / refresh_token

# 6. Agent Chat + WebSocket 测试
curl -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Authorization: Bearer <token>" \
  -d '{"message":"帮我复盘昨天的面试"}'
# → 返回 {"task_id":"xxx","status":"queued"}
# WebSocket: wscat -c ws://localhost:8000/ws/tasks/xxx
# → 接收 {"stage":"supervisor","delta":"..."} 等事件流

# 7. Memory 层集成测试
pytest backend/tests/test_memory.py -v

# 8. Tool 单元测试
pytest backend/tests/test_tools.py -v

# 9. embedding worker 测试
celery -A app.workers.celery_app call app.workers.embedding_worker.process_note_embedding \
  --args='["test-note-id","# 今日学习\n\nRedis 持久化"]'

# 10. Neo4j 节点验证
python -c "
import asyncio
from app.db.neo4j import init_neo4j, get_neo4j
async def check():
    await init_neo4j()
    async with get_neo4j().session() as s:
        r = await s.run('RETURN 1 AS ping')
        print(await r.single())
asyncio.run(check())
"

# 11. MCP Server smoke test
echo '{"method":"tools/list"}' | python -m app.agents.mcp_server
```

---

## 相关文档

- [step2-implementation-plan.md](step2-implementation-plan.md) — Step 2 骨架说明
- [architecture.md](architecture.md) — 系统架构 + 请求时序图
- [memory-system.md](memory-system.md) — 7 层 Cognitive Memory 规范
- [database-schema.md](database-schema.md) — 完整 DDL + ER 图
- [PLAN.md](../PLAN.md) — 全局开发计划
