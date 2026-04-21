"""
FastAPI Dependency: get_async_session
用法：
    async def endpoint(db: AsyncSession = Depends(get_async_session)):
        ...
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import AsyncSessionLocal


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """提供一个请求作用域的数据库会话，请求结束后自动关闭。"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
