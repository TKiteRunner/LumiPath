"""
Semantic Memory — Neo4j 图数据库。
负责：
  - 笔记 #tag → Concept 节点（write）
  - 用户已知概念检索（read）
  - 全文 / 关键词搜索 Concept（search）
"""
from __future__ import annotations

import structlog
from typing import Any

from app.agents.memory.base import BaseMemory
from app.db.neo4j import get_neo4j_session, is_neo4j_available, CONCEPT_FULLTEXT_INDEX

logger = structlog.get_logger(__name__)


class SemanticMemory(BaseMemory):

    async def read(self, key: str, top_k: int = 20, **kwargs) -> Any:
        """
        返回用户已 KNOWS 的 Concept 节点列表，按掌握次数降序。
        key 为 concept name 时精确查询单个节点及其邻居。
        """
        if not is_neo4j_available():
            return []

        async with get_neo4j_session() as session:
            if key:
                result = await session.run(
                    """
                    MATCH (u:User {id: $uid})-[r:KNOWS]->(c:Concept {name: $name})
                    OPTIONAL MATCH (c)-[:RELATED_TO]->(related:Concept)
                    RETURN c.name AS concept, r.count AS freq, collect(related.name) AS related
                    """,
                    uid=self.user_id, name=key,
                )
                records = await result.data()
            else:
                result = await session.run(
                    """
                    MATCH (u:User {id: $uid})-[r:KNOWS]->(c:Concept)
                    RETURN c.name AS concept, r.count AS freq
                    ORDER BY r.count DESC
                    LIMIT $k
                    """,
                    uid=self.user_id, k=top_k,
                )
                records = await result.data()
        return records

    async def write(self, data: dict, **kwargs) -> None:
        """
        将 tags 列表写入 Neo4j，MERGE Concept 节点并更新 KNOWS 关系计数。
        data 需含：tags (list[str])，可选 note_id (str)。
        """
        tags: list[str] = data.get("tags", [])
        if not tags or not is_neo4j_available():
            return

        async with get_neo4j_session() as session:
            # 确保 User 节点存在
            await session.run(
                "MERGE (u:User {id: $uid})",
                uid=self.user_id,
            )
            # 批量 MERGE Concept + KNOWS 关系
            for tag in tags:
                if not tag:
                    continue
                await session.run(
                    """
                    MATCH (u:User {id: $uid})
                    MERGE (c:Concept {name: $tag})
                    MERGE (u)-[r:KNOWS]->(c)
                    ON CREATE SET r.count = 1, r.first_seen = datetime()
                    ON MATCH  SET r.count = r.count + 1, r.last_seen = datetime()
                    """,
                    uid=self.user_id, tag=tag,
                )
            # 若提供 note_id，建立 Note → Concept 关系
            note_id = data.get("note_id")
            if note_id:
                for tag in tags:
                    if not tag:
                        continue
                    await session.run(
                        """
                        MERGE (n:Note {id: $nid})
                        MERGE (c:Concept {name: $tag})
                        MERGE (n)-[:TAGGED_WITH]->(c)
                        """,
                        nid=note_id, tag=tag,
                    )
        logger.debug("SemanticMemory.write", user_id=self.user_id, tags=tags)

    async def search(self, query: str, top_k: int = 5, **kwargs) -> list[dict]:
        """
        全文检索 Concept 节点（Neo4j fulltext index），
        再过滤该用户 KNOWS 的节点并按掌握频次加权排序。
        """
        if not is_neo4j_available():
            return []

        try:
            async with get_neo4j_session() as session:
                result = await session.run(
                    f"""
                    CALL db.index.fulltext.queryNodes("{CONCEPT_FULLTEXT_INDEX}", $query)
                    YIELD node AS c, score AS ft_score
                    OPTIONAL MATCH (u:User {{id: $uid}})-[r:KNOWS]->(c)
                    RETURN c.name AS concept,
                           ft_score,
                           coalesce(r.count, 0) AS freq,
                           (ft_score + coalesce(r.count, 0) * 0.1) AS combined_score
                    ORDER BY combined_score DESC
                    LIMIT $k
                    """,
                    query=query, uid=self.user_id, k=top_k,
                )
                records = await result.data()
            logger.debug("SemanticMemory.search", user_id=self.user_id, query=query[:50], hits=len(records))
            return records
        except Exception as exc:
            logger.warning("SemanticMemory.search failed", error=str(exc))
            return []

    async def add_concept_relation(self, from_concept: str, to_concept: str, rel_type: str = "RELATED_TO") -> None:
        """在两个 Concept 之间建立关系（用于笔记 wikilink 解析）。"""
        if not is_neo4j_available():
            return
        async with get_neo4j_session() as session:
            await session.run(
                f"""
                MERGE (a:Concept {{name: $from_c}})
                MERGE (b:Concept {{name: $to_c}})
                MERGE (a)-[:{rel_type}]->(b)
                """,
                from_c=from_concept, to_c=to_concept,
            )
