"""
Celery 配置及实例化，4个并发队列。
"""
from celery import Celery
from kombu import Queue, Exchange

from app.config import settings

celery_app = Celery(
    "lumipath",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.embedding_worker", "app.workers.vault_watcher"]
)

# 定制 4 个队列进行任务分流：
# 1. agent_long (AI 推理, 面试复盘)
# 2. embedding (计算文档向量)
# 3. vault_sync (Git clone & push, 本地文件同步)
# 4. notify (发邮件推送 websocket)
celery_app.conf.task_queues = (
    Queue('agent_long', Exchange('agent_long'), routing_key='agent_long'),
    Queue('embedding', Exchange('embedding'), routing_key='embedding'),
    Queue('vault_sync', Exchange('vault_sync'), routing_key='vault_sync'),
    Queue('notify', Exchange('notify'), routing_key='notify'),
)

celery_app.conf.task_routes = {
    'app.workers.embedding_worker.*': {'queue': 'embedding'},
    'app.workers.vault_watcher.*': {'queue': 'vault_sync'},
    'app.workers.agent_worker.*': {'queue': 'agent_long'},
}

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_acks_late=True,  # 执行完才清理，保证不丢失
)
