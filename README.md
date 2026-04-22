# LumiPath AI-driven personal growth OS

LumiPath 是一款由本地/云端 LLM 驱动的个人成长数字大脑（操作系统），深度融合了面试追踪、OKR 目标管理、笔记（知识图谱）与长期个人记忆画像。

## 架构特色

*   **真正的多智能体 (Multi-Agent)**: 采用 LangGraph 构建 Supervisor + 4 专家 Agent（Interview, OKR, Notes, Memory）的路由架构。
*   **7 层认知记忆系统**: 结合工作记忆 (In-Context)、短期缓存 (Redis)、长期画像 (PostgreSQL JSONB)、情景记忆/压缩摘要 (pgvector) 与语义图谱 (Neo4j)。
*   **Markdown-first Vault (知识库)**: 用户的笔记以纯平文本 `.md` 存放在本地/Git，与后端实现双向同步，保护数据主权，并支持 Obsidian 直接读取。
*   **Skill 与 MCP**: 工具调用层抽象为 Tools，业务流程提纯为 Vault 中的 Markdown Skills；预留 MCP Server 接口以供外部 AI 助手访问。
*   **隐私与安全**: 用户的 API Key 在数据库中使用 `pgcrypto` 主密钥进行加密隔离存储，敏感日志脱敏，全面支持本地大模型推理。

## 技术栈 (Step 2 - Backend)

*   **语言**: Python 3.12+
*   **API 框架**: FastAPI + Uvicorn
*   **图谱/多智能体引擎**: LangGraph + LangChain Core
*   **ORM 与数据库**: SQLAlchemy 2.0 (Async) + asyncpg + Alembic + PostgreSQL 16 + pgvector
*   **异步任务**: Celery + RabbitMQ + Redis
*   **类型检查**: Pydantic v2 + Ruff + mypy

## 本地启动指南

### 前置条件

- Docker Desktop（已启动）
- 准备好 LLM API Key（OpenAI / Anthropic / DeepSeek 等）

### 第一步：环境变量

```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入 APP_SECRET_KEY、APP_MASTER_KEY 和至少一个 LLM API Key
```

### 第二步：构建镜像

**普通构建**（apt/pip 走阿里云镜像，无需代理）：
```bash
docker compose build
```

**代理构建**（网络受 VPN/Clash Fake-IP 影响时使用，端口按实际修改）：
```bash
docker compose build --build-arg HTTP_PROXY=http://host.docker.internal:7890 --build-arg HTTPS_PROXY=http://host.docker.internal:7890
```

### 第三步：启动基础设施

```bash
docker compose up -d db redis rabbitmq neo4j
# 等待约 30 秒，确认全部 healthy
docker compose ps
```

### 第四步：数据库迁移（首次执行一次）

```bash
docker compose run --rm migrate
```

### 第五步：启动后端与 Worker

```bash
docker compose up -d backend worker
docker compose logs -f backend   # 看到 "Application startup complete." 即成功
```

### 常用访问地址

| 服务 | 地址 |
|------|------|
| API 文档 | http://localhost:8000/docs |
| RabbitMQ 管理 UI | http://localhost:15672 (guest/guest) |
| Neo4j Browser | http://localhost:17474 (neo4j/lumipath_dev_password) |

### 常用命令

```bash
docker compose ps                     # 查看所有容器状态
docker compose logs -f backend        # 实时日志
docker compose down                   # 停止（保留数据）
docker compose down -v                # 停止并清除所有数据（慎用）
docker compose build backend worker   # 仅重建后端镜像
```
