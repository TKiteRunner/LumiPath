"""
Vault 文件 ↔ DB 双向同步 + Git 操作（骨架）
Step 3 完善 watchfiles 监听和 Git push。
"""
from __future__ import annotations

from pathlib import Path

import structlog

from app.config import settings

logger = structlog.get_logger(__name__)


class VaultSyncService:
    """封装 vault 的 Git 操作和文件 ↔ DB 同步逻辑。"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.vault_path = Path(settings.vault_base_path) / str(user_id)

    def ensure_vault_initialized(self) -> None:
        """确保 vault 目录存在且已初始化 Git 仓库。"""
        self.vault_path.mkdir(parents=True, exist_ok=True)
        git_dir = self.vault_path / ".git"
        if not git_dir.exists():
            self._git_init()

    def _git_init(self) -> None:
        """初始化 Git 仓库。"""
        # TODO Step 3: 使用 GitPython
        # import git; git.Repo.init(str(self.vault_path))
        logger.info("git init (stub)", path=str(self.vault_path))

    def commit(self, message: str) -> None:
        """提交 vault 中的变更。"""
        # TODO Step 3:
        # repo = git.Repo(str(self.vault_path))
        # repo.git.add(A=True)
        # if repo.is_dirty():
        #     repo.index.commit(message)
        logger.info("git commit (stub)", message=message)

    def push(self) -> None:
        """推送到远端。"""
        # TODO Step 3
        logger.info("git push (stub)")

    def pull(self) -> None:
        """从远端拉取（ff-only）。"""
        # TODO Step 3
        logger.info("git pull (stub)")
