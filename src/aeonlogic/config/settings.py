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

    # ── Runtime mode ──────────────────────────────────────────────────────────
    # "auto"  — use real Qwen if QWEN_API_KEY is set, else mock (default / backward-compat)
    # "real"  — explicitly require real Qwen; FALLBACK_MODE if key absent or call fails
    # "mock"  — always use the deterministic mock client regardless of key
    aeonlogic_mode: str = "auto"

    # ── Qwen / DashScope API ──────────────────────────────────────────────────
    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = ""           # optional override; falls back to budget model if empty
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
    def _mode(self) -> str:
        return self.aeonlogic_mode.strip().lower()

    @property
    def is_real_qwen_mode(self) -> bool:
        """True when a real Qwen client should and can be used.

        Backward-compatible: key present with aeonlogic_mode="auto" also returns True.
        """
        return self._mode in ("auto", "real") and bool(self.qwen_api_key.strip())

    @property
    def is_real_mode_explicitly_requested(self) -> bool:
        """True only when AEONLOGIC_MODE=real (not auto)."""
        return self._mode == "real"

    @property
    def client_mode_label(self) -> str:
        """Backward-compatible label.  Returns REAL_QWEN_MODE / MOCK_MODEL_MODE."""
        return "REAL_QWEN_MODE" if self.is_real_qwen_mode else "MOCK_MODEL_MODE"

    @property
    def runtime_mode_label(self) -> str:
        """Display label for Streamlit and Phase 6A+ UI.

        Returns one of: REAL_MODEL_MODE | MOCK_MODEL_MODE | FALLBACK_MODE.

        FALLBACK_MODE is returned when AEONLOGIC_MODE=real but no key is configured.
        After an actual pipeline run, use qwen_client.get_client_mode_label() for the
        post-run label (which may be FALLBACK_MODE if a live call failed).
        """
        if self.is_real_qwen_mode:
            return "REAL_MODEL_MODE"
        if self.is_real_mode_explicitly_requested:
            # real was requested but key is absent → pre-run fallback indicator
            return "FALLBACK_MODE"
        return "MOCK_MODEL_MODE"

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
