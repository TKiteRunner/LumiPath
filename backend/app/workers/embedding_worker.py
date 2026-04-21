"""任务：笔记向量嵌入与保存 pgvector"""
import structlog
from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(bind=True, max_retries=3)
def process_note_embedding(self, note_id: str, content: str):
    """
    1. 切块 chunk_text
    2. LiteLLM 生成向量
    3. 存入 pgvector `note_embeddings`
    """
    logger.info("process_note_embedding started", note_id=note_id)
    # TODO Step 3
    return {"status": "ok", "note_id": note_id}
