"""
LumiPath Backend Configuration
使用 pydantic-settings 从环境变量 / .env 文件中加载配置。
"""
from functools import lru_cache
from typing import Literal

from pydantic import AnyUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── 应用基础 ─────────────────────────────────────────────
    app_env: Literal["development", "staging", "production"] = "development"
    app_secret_key: str = "change-me"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_master_key: str = "change-me-pgcrypto-master-key"

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"

    # ── JWT ──────────────────────────────────────────────────
    jwt_access_expire_minutes: int = 15
    jwt_refresh_expire_days: int = 7
    jwt_algorithm: str = "HS256"

    # ── PostgreSQL ───────────────────────────────────────────
    database_url: str = (
        "postgresql+asyncpg://lumipath:lumipath_dev_password@localhost:5432/lumipath"
    )
    # 同步 URL 供 Celery worker 使用（psycopg2）
    database_url_sync: str = (
        "postgresql+psycopg2://lumipath:lumipath_dev_password@localhost:5432/lumipath"
    )

    # ── Redis ────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    redis_password: str = ""

    # ── Neo4j ────────────────────────────────────────────────
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "lumipath_dev_password"

    # ── RabbitMQ ─────────────────────────────────────────────
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672//"

    # ── LLM 兜底 Keys ────────────────────────────────────────
    fallback_anthropic_api_key: str = ""
    fallback_openai_api_key: str = ""
    fallback_deepseek_api_key: str = ""
    fallback_qwen_api_key: str = ""
    fallback_gemini_api_key: str = ""

    # ── Google OAuth ─────────────────────────────────────────
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"

    # ── Vault ────────────────────────────────────────────────
    vault_base_path: str = "./vault"
    vault_git_auto_commit: bool = True
    vault_git_commit_debounce_sec: int = 10

    # ── Celery ───────────────────────────────────────────────
    celery_broker_url: str = "amqp://guest:guest@localhost:5672//"
    celery_result_backend: str = "redis://localhost:6379/1"

    # ── MCP Server ───────────────────────────────────────────
    mcp_server_host: str = "0.0.0.0"
    mcp_server_port: int = 8765


@lru_cache
def get_settings() -> Settings:
    """返回缓存的 Settings 单例（import 时不执行，调用时才初始化）。"""
    return Settings()


# 方便直接 `from app.config import settings` 使用
settings = get_settings()
