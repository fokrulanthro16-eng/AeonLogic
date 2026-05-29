from __future__ import annotations

import logging

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Runtime configuration loaded from environment variables and .env file.
    All fields have safe defaults so the system works with zero configuration
    (falling back to MOCK_MODEL_MODE when QWEN_API_KEY is absent).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Qwen / DashScope API ──────────────────────────────────────────────────
    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_fast_model: str = "qwen-turbo"
    qwen_deep_model: str = "qwen-plus"

    # ── Neo4j Knowledge Graph ─────────────────────────────────────────────────
    neo4j_uri: str = ""
    neo4j_username: str = "neo4j"
    neo4j_password: str = ""

    # ── Application ───────────────────────────────────────────────────────────
    app_env: str = "development"
    log_level: str = "WARNING"

    # ── Derived properties ────────────────────────────────────────────────────

    @property
    def is_real_qwen_mode(self) -> bool:
        """True when a non-empty API key is configured."""
        return bool(self.qwen_api_key.strip())

    @property
    def client_mode_label(self) -> str:
        return "REAL_QWEN_MODE" if self.is_real_qwen_mode else "MOCK_MODEL_MODE"

    @property
    def effective_log_level(self) -> int:
        return getattr(logging, self.log_level.upper(), logging.WARNING)


# ── Module-level singleton ────────────────────────────────────────────────────

_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Clear cached settings instance. Use in tests only."""
    global _settings
    _settings = None
