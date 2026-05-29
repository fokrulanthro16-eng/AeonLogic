"""Phase 6A: Real Qwen cloud mode — unit tests.

All tests run without a real API key or network connection.
ResilientQwenClient fallback is verified with a stub that raises.
"""
from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import Any

import pytest

import importlib.util

from aeonlogic.config.settings import get_settings, reset_settings
from aeonlogic.models.qwen_client import (
    MockQwenClient,
    QwenClient,
    ResilientQwenClient,
    _set_active_mode,
    get_client,
    get_client_mode_label,
)
from aeonlogic.models.budgets import ModelBudget

_OPENAI_AVAILABLE = importlib.util.find_spec("openai") is not None


# ---------------------------------------------------------------------------
# Helpers and fixtures
# ---------------------------------------------------------------------------

def _budget() -> ModelBudget:
    return ModelBudget(
        model_name="qwen-turbo",
        max_tokens=512,
        temperature=0.0,
    )


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_settings()
    _set_active_mode("mock")
    yield
    reset_settings()
    _set_active_mode("mock")


# ---------------------------------------------------------------------------
# Settings — new fields
# ---------------------------------------------------------------------------

def test_settings_has_aeonlogic_mode_field() -> None:
    s = get_settings()
    assert hasattr(s, "aeonlogic_mode")


def test_settings_aeonlogic_mode_default_is_auto() -> None:
    s = get_settings()
    assert s.aeonlogic_mode.lower() == "auto"


def test_settings_has_qwen_model_field() -> None:
    s = get_settings()
    assert hasattr(s, "qwen_model")
    assert isinstance(s.qwen_model, str)


def test_settings_qwen_model_default_is_empty() -> None:
    assert get_settings().qwen_model == ""


def test_settings_qwen_base_url_is_international() -> None:
    url = get_settings().qwen_base_url
    assert "intl" in url or "international" in url.lower() or "dashscope-intl" in url


def test_settings_has_runtime_mode_label_property() -> None:
    assert hasattr(get_settings(), "runtime_mode_label")


# ---------------------------------------------------------------------------
# Settings — runtime_mode_label
# ---------------------------------------------------------------------------

def test_runtime_mode_label_mock_when_no_key_auto_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AEONLOGIC_MODE", "auto")
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    reset_settings()
    assert get_settings().runtime_mode_label == "MOCK_MODEL_MODE"


def test_runtime_mode_label_real_when_key_present_auto_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AEONLOGIC_MODE", "auto")
    monkeypatch.setenv("QWEN_API_KEY", "sk-test-abc123")
    reset_settings()
    assert get_settings().runtime_mode_label == "REAL_MODEL_MODE"


def test_runtime_mode_label_real_when_mode_real_and_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AEONLOGIC_MODE", "real")
    monkeypatch.setenv("QWEN_API_KEY", "sk-test-abc123")
    reset_settings()
    assert get_settings().runtime_mode_label == "REAL_MODEL_MODE"


def test_runtime_mode_label_fallback_when_mode_real_no_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AEONLOGIC_MODE", "real")
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    reset_settings()
    assert get_settings().runtime_mode_label == "FALLBACK_MODE"


def test_runtime_mode_label_mock_when_mode_mock_even_with_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AEONLOGIC_MODE", "mock")
    monkeypatch.setenv("QWEN_API_KEY", "sk-test-abc123")
    reset_settings()
    assert get_settings().runtime_mode_label == "MOCK_MODEL_MODE"


# ---------------------------------------------------------------------------
# Settings — client_mode_label backward compatibility
# ---------------------------------------------------------------------------

def test_client_mode_label_backward_compat_no_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    reset_settings()
    assert get_settings().client_mode_label == "MOCK_MODEL_MODE"


def test_client_mode_label_backward_compat_key_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("QWEN_API_KEY", "sk-test-abc123")
    reset_settings()
    # With auto mode (default) + key → REAL_QWEN_MODE (unchanged from pre-6A)
    assert get_settings().client_mode_label == "REAL_QWEN_MODE"


# ---------------------------------------------------------------------------
# get_client() — mock mode
# ---------------------------------------------------------------------------

def test_get_client_returns_mock_when_mode_mock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AEONLOGIC_MODE", "mock")
    monkeypatch.setenv("QWEN_API_KEY", "sk-test-abc123")
    reset_settings()
    client = get_client()
    assert isinstance(client, MockQwenClient)


def test_get_client_sets_active_mode_mock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AEONLOGIC_MODE", "mock")
    reset_settings()
    get_client()
    assert get_client_mode_label() == "MOCK_MODEL_MODE"


def test_get_client_returns_mock_when_no_key_auto_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AEONLOGIC_MODE", "auto")
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    reset_settings()
    client = get_client()
    assert isinstance(client, MockQwenClient)
    assert get_client_mode_label() == "MOCK_MODEL_MODE"


# ---------------------------------------------------------------------------
# get_client() — fallback when real requested but key absent
# ---------------------------------------------------------------------------

def test_get_client_returns_mock_fallback_when_mode_real_no_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AEONLOGIC_MODE", "real")
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    reset_settings()
    client = get_client()
    assert isinstance(client, MockQwenClient)


def test_get_client_sets_fallback_mode_when_real_no_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AEONLOGIC_MODE", "real")
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    reset_settings()
    get_client()
    assert get_client_mode_label() == "FALLBACK_MODE"


# ---------------------------------------------------------------------------
# get_client() — real mode with key (no network call in test)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _OPENAI_AVAILABLE, reason="openai package not installed")
def test_get_client_returns_resilient_client_when_real_mode_with_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AEONLOGIC_MODE", "real")
    monkeypatch.setenv("QWEN_API_KEY", "sk-test-abc123")
    reset_settings()
    # Patch openai.OpenAI so the constructor does not validate the fake key
    import openai as _openai_mod
    monkeypatch.setattr(_openai_mod, "OpenAI", lambda **kw: SimpleNamespace())
    client = get_client()
    assert isinstance(client, ResilientQwenClient)
    assert get_client_mode_label() == "REAL_MODEL_MODE"


@pytest.mark.skipif(not _OPENAI_AVAILABLE, reason="openai package not installed")
def test_get_client_returns_resilient_client_auto_mode_with_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AEONLOGIC_MODE", "auto")
    monkeypatch.setenv("QWEN_API_KEY", "sk-test-abc123")
    reset_settings()
    import openai as _openai_mod
    monkeypatch.setattr(_openai_mod, "OpenAI", lambda **kw: SimpleNamespace())
    client = get_client()
    assert isinstance(client, ResilientQwenClient)


def test_get_client_real_mode_with_key_is_resilient_or_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When real mode + key are set, result is ResilientQwenClient (openai present)
    or MockQwenClient with FALLBACK_MODE (openai absent). Never plain mock."""
    monkeypatch.setenv("AEONLOGIC_MODE", "real")
    monkeypatch.setenv("QWEN_API_KEY", "sk-test-abc123")
    reset_settings()
    client = get_client()
    mode = get_client_mode_label()
    assert isinstance(client, (ResilientQwenClient, MockQwenClient))
    assert mode in ("REAL_MODEL_MODE", "FALLBACK_MODE")


# ---------------------------------------------------------------------------
# get_client() — fallback when openai package not importable
# ---------------------------------------------------------------------------

def test_get_client_falls_back_when_openai_not_importable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AEONLOGIC_MODE", "real")
    monkeypatch.setenv("QWEN_API_KEY", "sk-test-abc123")
    reset_settings()
    monkeypatch.setitem(sys.modules, "openai", None)  # type: ignore[arg-type]
    client = get_client()
    assert isinstance(client, MockQwenClient)
    assert get_client_mode_label() == "FALLBACK_MODE"


# ---------------------------------------------------------------------------
# ResilientQwenClient — fallback on exception
# ---------------------------------------------------------------------------

class _BrokenRealClient:
    """Stub that always raises to simulate a failed real API call."""

    def complete(self, budget: ModelBudget, prompt: str) -> str:
        raise RuntimeError("Simulated API failure")


def test_resilient_client_falls_back_to_mock_on_exception() -> None:
    real = _BrokenRealClient()  # type: ignore[arg-type]
    resilient = ResilientQwenClient(real)  # type: ignore[arg-type]
    result = resilient.complete(_budget(), "auth login test")
    # Should return mock output — not raise
    assert isinstance(result, str)
    assert len(result) > 0


def test_resilient_client_sets_fallback_mode_on_exception() -> None:
    real = _BrokenRealClient()  # type: ignore[arg-type]
    resilient = ResilientQwenClient(real)  # type: ignore[arg-type]
    _set_active_mode("real")
    resilient.complete(_budget(), "auth login test")
    assert get_client_mode_label() == "FALLBACK_MODE"


def test_resilient_client_returns_mock_content_on_exception() -> None:
    real = _BrokenRealClient()  # type: ignore[arg-type]
    resilient = ResilientQwenClient(real)  # type: ignore[arg-type]
    result = resilient.complete(_budget(), "auth login token")
    # Mock returns auth-specific content for auth prompts
    assert "auth" in result.lower() or "jwt" in result.lower() or "login" in result.lower()


# ---------------------------------------------------------------------------
# get_client_mode_label
# ---------------------------------------------------------------------------

def test_get_client_mode_label_default_is_mock() -> None:
    _set_active_mode("mock")
    assert get_client_mode_label() == "MOCK_MODEL_MODE"


def test_get_client_mode_label_real() -> None:
    _set_active_mode("real")
    assert get_client_mode_label() == "REAL_MODEL_MODE"


def test_get_client_mode_label_fallback() -> None:
    _set_active_mode("fallback")
    assert get_client_mode_label() == "FALLBACK_MODE"


# ---------------------------------------------------------------------------
# QWEN_MODEL override
# ---------------------------------------------------------------------------

def test_qwen_model_setting_can_be_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QWEN_MODEL", "qwen-max")
    reset_settings()
    assert get_settings().qwen_model == "qwen-max"


def test_qwen_model_default_is_empty() -> None:
    assert get_settings().qwen_model == ""
