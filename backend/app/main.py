"""
LumiPath FastAPI Application Entry Point
"""
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.db.engine import engine
from app.db.redis import init_redis_pool, close_redis_pool, get_redis, bloom_init
from app.db.neo4j import init_neo4j, close_neo4j

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化所有外部连接，关闭时清理。"""
    logger.info("LumiPath backend starting", env=settings.app_env)

    # Redis
    await init_redis_pool()
    redis = get_redis()
    await bloom_init(redis)
    logger.info("Redis pool initialized")

    # Neo4j
    await init_neo4j()

    yield

    # 关闭
    await close_redis_pool()
    await close_neo4j()
    await engine.dispose()
    logger.info("LumiPath backend shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="LumiPath API",
        description="AI-driven personal growth OS — Backend",
        version="0.1.0",
        docs_url="/docs" if settings.is_dev else None,
        redoc_url="/redoc" if settings.is_dev else None,
        lifespan=lifespan,
    )

    # ── CORS（开发阶段宽松，生产限制 origin）─────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.is_dev else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── 异常 handler ──────────────────────────────────────────────
    register_exception_handlers(app)

    # ── 路由 ──────────────────────────────────────────────────────
    app.include_router(api_router)

    # ── Health check ─────────────────────────────────────────────
    @app.get("/health", tags=["infra"])
    async def health():
        return {"status": "ok", "env": settings.app_env}

    return app


app = create_app()
