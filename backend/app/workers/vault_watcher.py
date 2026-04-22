"""
Celery Tasks: Vault 文件同步
- sync_vault            : Git add/commit/push（由 API 触发或定时调用）
- trigger_db_sync_for_file : 外部文件变更（Obsidian 编辑）→ 解析 → 回流 DB + 重新 embedding
- start_vault_watcher   : 长驻进程，watchfiles 监听目录变更（supervisord 管理）
"""
from __future__ import annotations

import structlog

from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


# ── Git 同步 ──────────────────────────────────────────────────────────────────

@celery_app.task(bind=True, max_retries=2, default_retry_delay=10)
def sync_vault(self, user_id: str, message: str = "auto: sync vault"):
    """Git add → commit → （可选）push。"""
    from app.config import settings
    from pathlib import Path

    vault_path = Path(settings.vault_base_path) / user_id
    if not vault_path.exists():
        logger.warning("vault path not found, skipping git sync", user_id=user_id)
        return {"status": "skipped", "reason": "vault not found"}

    if not settings.vault_git_auto_commit:
        return {"status": "skipped", "reason": "git auto commit disabled"}

    try:
        import git
        try:
            repo = git.Repo(vault_path)
        except git.InvalidGitRepositoryError:
            repo = git.Repo.init(vault_path)
            logger.info("vault git repo initialized", user_id=user_id)

        repo.git.add(A=True)
        if repo.is_dirty(index=True) or repo.untracked_files:
            repo.index.commit(message)
            logger.info("vault committed", user_id=user_id, message=message)
            return {"status": "committed", "message": message}
        return {"status": "clean", "message": "nothing to commit"}
    except Exception as exc:
        logger.error("vault sync failed", user_id=user_id, error=str(exc))
        raise self.retry(exc=exc)


# ── 文件 → DB 回流 ────────────────────────────────────────────────────────────

@celery_app.task
def trigger_db_sync_for_file(user_id: str, file_path: str, event_type: str):
    """
    外部文件变更（Obsidian 编辑）回流：
    1. 读取文件内容
    2. 解析 frontmatter / wikilinks / tags
    3. 同步写入 DB（同步 session）
    4. 触发 embedding 重新计算
    """
    from pathlib import Path
    from app.services.notes_service import parse_note, NotesService, read_note_file
    from app.config import settings

    p = Path(file_path)
    if not p.exists() or p.suffix != ".md" or p.name.endswith(".conflict"):
        logger.info("skip non-md or conflict file", file_path=file_path)
        return {"status": "skipped", "file": file_path}

    content = read_note_file(p)
    if not content:
        return {"status": "skipped", "reason": "empty file"}

    parsed = parse_note(content)

    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session
        from app.config import settings as _settings

        engine = create_engine(_settings.database_url_sync, pool_pre_ping=True)
        with Session(engine) as db:
            svc = NotesService()
            svc.upsert_from_file_path_sync(
                user_id=user_id,
                file_path=file_path,
                parsed=parsed,
                db=db,
            )
    except Exception as exc:
        logger.error("trigger_db_sync_for_file DB upsert failed", file=file_path, error=str(exc))
        return {"status": "error", "error": str(exc)}

    # 触发重新 embedding（异步，不阻塞本任务）
    try:
        from app.workers.embedding_worker import process_note_embedding
        # 用文件 stem 作为临时 note_id，后续可从 DB 拿真实 UUID
        process_note_embedding.apply_async(
            args=[str(p.stem), content],
            queue="embedding",
        )
    except Exception as exc:
        logger.warning("failed to enqueue embedding", file=file_path, error=str(exc))

    logger.info("trigger_db_sync_for_file done", user_id=user_id, file=file_path, event=event_type)
    return {"status": "ok", "file": file_path, "tags": parsed.tags}


# ── 长驻监听进程 ──────────────────────────────────────────────────────────────

def start_vault_watcher(user_id: str) -> None:
    """
    长驻进程：用 watchfiles 监听 vault 目录，变更触发 Celery 任务。
    由 supervisord 管理（见 infra/supervisord.conf）。
    """
    from app.config import settings
    from pathlib import Path

    watch_path = Path(settings.vault_base_path) / user_id
    watch_path.mkdir(parents=True, exist_ok=True)

    try:
        from watchfiles import watch, Change
        logger.info("vault watcher started", path=str(watch_path), user_id=user_id)
        for changes in watch(str(watch_path)):
            for change_type, changed_path in changes:
                if not changed_path.endswith(".md"):
                    continue
                if changed_path.endswith(".md.tmp") or ".conflict" in changed_path:
                    continue
                event_type = {
                    Change.added: "added",
                    Change.modified: "modified",
                    Change.deleted: "deleted",
                }.get(change_type, "unknown")

                if event_type == "deleted":
                    # 软删除由 DB 端处理，暂不 trigger
                    continue

                trigger_db_sync_for_file.apply_async(
                    args=[user_id, changed_path, event_type],
                    queue="vault_sync",
                )
                logger.debug("vault change detected", file=changed_path, event=event_type)
    except Exception as exc:
        logger.error("vault watcher crashed", user_id=user_id, error=str(exc))
        raise
