"""
Async SQLAlchemy Engine + Session Factory
"""
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# ── Engine ────────────────────────────────────────────────────────────────────
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.is_dev,          # SQL 日志只在 dev 输出
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,            # 检测断连
)

# ── Session Factory ───────────────────────────────────────────────────────────
AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,        # 避免 lazy-load 在 async 中出错
    autocommit=False,
    autoflush=False,
)
