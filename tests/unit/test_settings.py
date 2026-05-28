"""Unit tests: Settings loading, client mode selection, mock fallback."""
from __future__ import annotations

import pytest

from aeonlogic.config.settings import Settings


# ── Settings defaults ─────────────────────────────────────────────────────────

def test_default_fast_model_is_qwen_turbo() -> None:
    s = Settings(qwen_api_key="")
    assert s.qwen_fast_model == "qwen-turbo"


def test_default_deep_model_is_qwen_plus() -> None:
    s = Settings(qwen_api_key="")
    assert s.qwen_deep_model == "qwen-plus"


def test_default_app_env_is_development() -> None:
    s = Settings(qwen_api_key="")
    assert s.app_env == "development"


def test_default_base_url_points_to_dashscope() -> None:
    s = Settings(qwen_api_key="")
    assert "dashscope" in s.qwen_base_url


# ── Mock / real mode detection ────────────────────────────────────────────────

def test_empty_api_key_is_mock_mode() -> None:
    s = Settings(qwen_api_key="")
    assert not s.is_real_qwen_mode


def test_whitespace_api_key_is_mock_mode() -> None:
    s = Settings(qwen_api_key="   ")
    assert not s.is_real_qwen_mode


def test_non_empty_api_key_activates_real_mode() -> None:
    s = Settings(qwen_api_key="sk-test-key-abc123")
    assert s.is_real_qwen_mode


def test_client_mode_label_when_no_key() -> None:
    s = Settings(qwen_api_key="")
    assert s.client_mode_label == "MOCK_MODEL_MODE"


def test_client_mode_label_when_key_present() -> None:
    s = Settings(qwen_api_key="sk-test-key")
    assert s.client_mode_label == "REAL_QWEN_MODE"


# ── get_client() mock fallback ────────────────────────────────────────────────

def test_get_client_returns_mock_when_api_key_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    import aeonlogic.config.settings as cfg_module
    from aeonlogic.models.qwen_client import MockQwenClient, get_client

    # Override the cached settings singleton with a no-key instance
    monkeypatch.setattr(cfg_module, "_settings", Settings(qwen_api_key=""))
    assert isinstance(get_client(), MockQwenClient)


def test_get_client_returns_mock_protocol_compliant(monkeypatch: pytest.MonkeyPatch) -> None:
    import aeonlogic.config.settings as cfg_module
    from aeonlogic.models.qwen_client import ModelClientProtocol, get_client

    monkeypatch.setattr(cfg_module, "_settings", Settings(qwen_api_key=""))
    client = get_client()
    assert isinstance(client, ModelClientProtocol)


# ── Protocol compliance ───────────────────────────────────────────────────────

def test_mock_client_satisfies_protocol() -> None:
    from aeonlogic.models.qwen_client import MockQwenClient, ModelClientProtocol

    assert isinstance(MockQwenClient(), ModelClientProtocol)


def test_qwen_client_class_is_importable() -> None:
    from aeonlogic.models.qwen_client import QwenClient  # noqa: F401

    assert QwenClient is not None


# ── budgets.py reads from settings ───────────────────────────────────────────

def test_budget_fast_model_matches_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    import aeonlogic.config.settings as cfg_module
    from aeonlogic.domain.task import ModelTier
    from aeonlogic.models.budgets import get_budget

    monkeypatch.setattr(cfg_module, "_settings", Settings(qwen_fast_model="custom-turbo"))
    budget = get_budget(ModelTier.FAST)
    assert budget.model_name == "custom-turbo"


def test_budget_deep_model_matches_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    import aeonlogic.config.settings as cfg_module
    from aeonlogic.domain.task import ModelTier
    from aeonlogic.models.budgets import get_budget

    monkeypatch.setattr(cfg_module, "_settings", Settings(qwen_deep_model="custom-plus"))
    budget = get_budget(ModelTier.STRONG)
    assert budget.model_name == "custom-plus"


# ── Dispatcher still routes correctly ─────────────────────────────────────────

def test_dispatcher_routes_auth_task_to_strong_model() -> None:
    from aeonlogic.agents.dispatcher import _classify_risk
    from aeonlogic.domain.task import ModelTier, RiskLevel
    from aeonlogic.models.router import route_model

    risk = _classify_risk("Build a secure API authentication module")
    tier = route_model(risk)
    assert risk == RiskLevel.HIGH
    assert tier == ModelTier.STRONG


# ── CLI client mode label is visible ─────────────────────────────────────────

def test_cli_shows_mock_model_mode_when_no_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    import aeonlogic.config.settings as cfg_module
    from aeonlogic.app.cli import app
    from typer.testing import CliRunner

    monkeypatch.setattr(cfg_module, "_settings", Settings(qwen_api_key=""))
    result = CliRunner().invoke(app, ["Build a secure API authentication module"])
    assert "MOCK_MODEL_MODE" in result.output
