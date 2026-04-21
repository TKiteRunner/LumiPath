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

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时连接检查，关闭时清理。"""
    logger.info("LumiPath backend starting", env=settings.app_env)
    # TODO Step 3: 初始化 Redis 连接池 / Neo4j 驱动 / RabbitMQ 连接
    yield
    # 关闭
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
