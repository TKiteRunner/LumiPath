"""
Neo4j async driver 单例 + session 工厂。
在 FastAPI lifespan 中调用 init_neo4j() / close_neo4j()。
"""
from __future__ import annotations

import structlog
from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncSession

from app.config import settings

logger = structlog.get_logger(__name__)

_driver: AsyncDriver | None = None

# ── 全文索引名称（SemanticMemory 用）──────────────────────────────────────────
CONCEPT_FULLTEXT_INDEX = "concept_name_idx"


# ── 生命周期 ──────────────────────────────────────────────────────────────────

async def init_neo4j() -> None:
    global _driver
    _driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
        max_connection_pool_size=10,
        connection_timeout=5,
    )
    try:
        await _driver.verify_connectivity()
        logger.info("Neo4j connected", uri=settings.neo4j_uri)
        await _ensure_indexes()
    except Exception as exc:
        logger.warning("Neo4j connection failed — semantic memory will be unavailable", error=str(exc))


async def close_neo4j() -> None:
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None
        logger.info("Neo4j driver closed")


def get_neo4j() -> AsyncDriver:
    if _driver is None:
        raise RuntimeError("Neo4j driver not initialized")
    return _driver


def get_neo4j_session(**kwargs: object) -> AsyncSession:
    return get_neo4j().session(**kwargs)


def is_neo4j_available() -> bool:
    return _driver is not None


# ── 索引初始化 ────────────────────────────────────────────────────────────────

async def _ensure_indexes() -> None:
    """确保 Concept 全文索引存在（幂等）。"""
    async with get_neo4j_session() as session:
        # 全文索引
        await session.run(
            f"""
            CREATE FULLTEXT INDEX {CONCEPT_FULLTEXT_INDEX} IF NOT EXISTS
            FOR (n:Concept) ON EACH [n.name]
            """
        )
        # KNOWS 关系约束索引（用于按用户快速查询）
        await session.run(
            "CREATE INDEX user_id_idx IF NOT EXISTS FOR (n:User) ON (n.id)"
        )
        await session.run(
            "CREATE INDEX concept_name_idx2 IF NOT EXISTS FOR (n:Concept) ON (n.name)"
        )
    logger.info("Neo4j indexes ensured")
