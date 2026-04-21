"""任务：Git 同步。外部可以触发此任务。"""
import structlog
from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(bind=True)
def sync_vault(self, user_id: str, message: str):
    """Celery worker 拉取并提交 Vault 变更。"""
    logger.info("sync_vault triggered", user_id=user_id, message=message)
    # TODO Step 3
    return {"status": "ok"}
