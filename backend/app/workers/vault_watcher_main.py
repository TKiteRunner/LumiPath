"""
vault_watcher_main.py — 独立启动脚本（supervisord 调用）。
遍历 vault 目录下所有用户子目录，为每个用户启动一个监听线程。
"""
from __future__ import annotations

import os
import signal
import sys
import threading
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)


def _watch_user(user_id: str) -> None:
    from app.workers.vault_watcher import start_vault_watcher
    try:
        start_vault_watcher(user_id)
    except Exception as exc:
        logger.error("vault watcher thread died", user_id=user_id, error=str(exc))


def main() -> None:
    from app.config import settings

    vault_root = Path(settings.vault_base_path)
    vault_root.mkdir(parents=True, exist_ok=True)

    threads: list[threading.Thread] = []
    stop_event = threading.Event()

    def _shutdown(sig, frame):
        logger.info("vault_watcher_main received shutdown signal")
        stop_event.set()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    # 为每个已存在的用户目录启动一个监听线程
    user_dirs = [d for d in vault_root.iterdir() if d.is_dir()] if vault_root.exists() else []
    if not user_dirs:
        logger.info("No user vault dirs found; watching root for new dirs", root=str(vault_root))
        # 至少启动一个哨兵，防止 supervisord 认为进程立即退出
        user_dirs = [vault_root]

    for user_dir in user_dirs:
        user_id = user_dir.name
        t = threading.Thread(
            target=_watch_user,
            args=(user_id,),
            daemon=True,
            name=f"vault-watcher-{user_id}",
        )
        t.start()
        threads.append(t)
        logger.info("Started vault watcher thread", user_id=user_id)

    logger.info("vault_watcher_main running", thread_count=len(threads))
    stop_event.wait()


if __name__ == "__main__":
    main()
