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

## 本地启动指南 (待完善 Step 3)

1. 配置开发环境和依赖:
   ```bash
   cd backend
   pip install -e .[dev]
   ```
2. 启动中间件容器:
   ```bash
   # docker-compose up -d (PostgreSQL, Redis, RabbitMQ, Neo4j)
   ```
3. 数据库迁移:
   ```bash
   alembic upgrade head
   ```
4. 运行服务:
   ```bash
   uvicorn app.main:app --reload
   ```
