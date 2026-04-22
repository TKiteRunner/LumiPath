"""
Celery Task: 笔记向量嵌入 — 切块 → LiteLLM embedding → pgvector bulk upsert。
"""
from __future__ import annotations

import structlog

from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)

_CHUNK_SIZE = 512
_CHUNK_OVERLAP = 64
_DEFAULT_MODEL = "text-embedding-3-small"
_BATCH_SIZE = 20  # 每批 embedding 调用的 chunk 数


def _split_chunks(text: str, size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP) -> list[str]:
    """滑动窗口切块：段落优先，超长则截断。"""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= size:
            current = f"{current}\n\n{para}".strip() if current else para
        else:
            if current:
                chunks.append(current)
            if len(para) > size:
                for i in range(0, len(para), size - overlap):
                    chunks.append(para[i: i + size])
                current = para[-overlap:] if overlap else ""
            else:
                current = para
    if current:
        chunks.append(current)
    return chunks or [text[:size]]


def _strip_frontmatter(content: str) -> str:
    try:
        import frontmatter as fm
        return fm.loads(content).content
    except Exception:
        return content


def _batched(lst: list, n: int):
    for i in range(0, len(lst), n):
        yield lst[i: i + n]


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def process_note_embedding(self, note_id: str, content: str, model: str = _DEFAULT_MODEL):
    """
    1. 剥离 frontmatter → 切块
    2. LiteLLM batch embedding（每批 ≤ 20 chunk）
    3. pgvector bulk upsert（同步 psycopg2）
    """
    logger.info("process_note_embedding started", note_id=note_id, model=model)

    body = _strip_frontmatter(content)
    chunks = _split_chunks(body)
    logger.info("chunks created", note_id=note_id, chunk_count=len(chunks))

    # ── LiteLLM batch embedding ───────────────────────────────────────────────
    import litellm
    vectors: list[list[float]] = []
    try:
        for batch in _batched(chunks, _BATCH_SIZE):
            resp = litellm.embedding(model=model, input=batch)
            vectors.extend([item["embedding"] for item in resp.data])
    except Exception as exc:
        logger.error("embedding call failed", note_id=note_id, error=str(exc))
        raise self.retry(exc=exc)

    # ── pgvector bulk upsert ──────────────────────────────────────────────────
    try:
        from sqlalchemy import create_engine, text
        from app.config import settings

        engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
        with engine.begin() as conn:
            # 清除旧向量
            conn.execute(
                text("DELETE FROM note_embeddings WHERE note_id = :nid"),
                {"nid": note_id},
            )
            # 批量插入
            for i, (chunk_text, vector) in enumerate(zip(chunks, vectors)):
                vec_str = "[" + ",".join(str(v) for v in vector) + "]"
                conn.execute(
                    text("""
                        INSERT INTO note_embeddings (id, note_id, chunk_index, chunk_text, model_name, embedding, created_at, updated_at)
                        VALUES (gen_random_uuid(), :nid, :idx, :txt, :model, :vec::vector, now(), now())
                        ON CONFLICT (note_id, chunk_index, model_name) DO UPDATE SET
                            chunk_text = EXCLUDED.chunk_text,
                            embedding  = EXCLUDED.embedding,
                            updated_at = now()
                    """),
                    {"nid": note_id, "idx": i, "txt": chunk_text, "model": model, "vec": vec_str},
                )
        logger.info("process_note_embedding done", note_id=note_id, chunk_count=len(chunks))
    except Exception as exc:
        logger.error("pgvector upsert failed", note_id=note_id, error=str(exc))
        raise self.retry(exc=exc)

    return {"status": "ok", "note_id": note_id, "chunk_count": len(chunks)}
