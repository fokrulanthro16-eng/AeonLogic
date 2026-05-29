"""Phase 6B: Qwen Cloud status panel — unit tests.

No Streamlit runtime, no API key, no network calls required.
All tests exercise pure functions only.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from aeonlogic.models.qwen_client import mask_api_key
from aeonlogic.app.streamlit_demo import (
    QWEN_ACTIVATION_NOTE,
    build_qwen_cloud_status,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _settings(
    qwen_api_key: str = "",
    qwen_base_url: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    qwen_model: str = "",
    qwen_fast_model: str = "qwen-turbo",
    runtime_mode_label: str = "MOCK_MODEL_MODE",
) -> Any:
    return SimpleNamespace(
        qwen_api_key=qwen_api_key,
        qwen_base_url=qwen_base_url,
        qwen_model=qwen_model,
        qwen_fast_model=qwen_fast_model,
        runtime_mode_label=runtime_mode_label,
    )


# ---------------------------------------------------------------------------
# mask_api_key
# ---------------------------------------------------------------------------

def test_mask_empty_string_returns_not_set() -> None:
    assert mask_api_key("") == "NOT SET"


def test_mask_whitespace_returns_not_set() -> None:
    assert mask_api_key("   ") == "NOT SET"


def test_mask_short_key_returns_all_bullets() -> None:
    result = mask_api_key("sk-abc")
    assert "●" in result
    assert "sk-abc" not in result


def test_mask_short_key_length_not_revealed() -> None:
    r6 = mask_api_key("abcdef")
    r8 = mask_api_key("abcdefgh")
    # Both short keys → all bullets, lengths differ (no partial reveal)
    assert all(c == "●" for c in r6)
    assert all(c == "●" for c in r8)


def test_mask_normal_key_shows_prefix() -> None:
    result = mask_api_key("sk-abcdefghijklmnop1234")
    assert result.startswith("sk-a")


def test_mask_normal_key_shows_suffix() -> None:
    result = mask_api_key("sk-abcdefghijklmnop1234")
    assert result.endswith("1234")


def test_mask_normal_key_contains_bullets() -> None:
    result = mask_api_key("sk-abcdefghijklmnop1234")
    assert "●" in result


def test_mask_never_returns_full_key() -> None:
    key = "sk-abcdefghijklmnopqrstuvwxyz1234"
    assert mask_api_key(key) != key


def test_mask_visible_chars_at_most_eight() -> None:
    key = "sk-abcdefghijklmnopqrstuvwxyz1234"
    result = mask_api_key(key)
    visible = result.replace("●", "")
    assert len(visible) <= 8


def test_mask_returns_string() -> None:
    assert isinstance(mask_api_key("sk-somekey"), str)


# ---------------------------------------------------------------------------
# build_qwen_cloud_status — required keys
# ---------------------------------------------------------------------------

def test_status_has_all_required_keys() -> None:
    status = build_qwen_cloud_status(_settings())
    for key in (
        "runtime_mode", "configured_model", "base_url_configured",
        "api_key_present", "api_key_masked", "activation_note",
    ):
        assert key in status, f"Missing key: {key!r}"


# ---------------------------------------------------------------------------
# build_qwen_cloud_status — api_key_present
# ---------------------------------------------------------------------------

def test_api_key_present_false_when_empty() -> None:
    assert build_qwen_cloud_status(_settings(qwen_api_key=""))["api_key_present"] is False


def test_api_key_present_false_when_whitespace() -> None:
    assert build_qwen_cloud_status(_settings(qwen_api_key="   "))["api_key_present"] is False


def test_api_key_present_true_when_key_set() -> None:
    assert build_qwen_cloud_status(_settings(qwen_api_key="sk-test123"))["api_key_present"] is True


# ---------------------------------------------------------------------------
# build_qwen_cloud_status — api_key_masked (never the real key)
# ---------------------------------------------------------------------------

def test_api_key_masked_never_equals_full_key() -> None:
    key = "sk-abcdefghijklmnopqrstuvwxyz1234"
    status = build_qwen_cloud_status(_settings(qwen_api_key=key))
    assert status["api_key_masked"] != key


def test_api_key_masked_shows_not_set_when_absent() -> None:
    status = build_qwen_cloud_status(_settings(qwen_api_key=""))
    assert status["api_key_masked"] == "NOT SET"


def test_api_key_masked_contains_bullets_when_key_present() -> None:
    status = build_qwen_cloud_status(_settings(qwen_api_key="sk-abcdefghijklmnop1234"))
    assert "●" in status["api_key_masked"]


def test_api_key_value_not_in_any_status_field() -> None:
    """The full key must not appear in any value in the status dict."""
    key = "sk-supersecretkey1234567890abcdef"
    status = build_qwen_cloud_status(_settings(qwen_api_key=key))
    for field_name, value in status.items():
        assert key not in str(value), f"Key leaked in field {field_name!r}"


# ---------------------------------------------------------------------------
# build_qwen_cloud_status — base_url_configured
# ---------------------------------------------------------------------------

def test_base_url_configured_true_when_url_present() -> None:
    s = _settings(qwen_base_url="https://dashscope-intl.aliyuncs.com/v1")
    assert build_qwen_cloud_status(s)["base_url_configured"] is True


def test_base_url_configured_false_when_url_empty() -> None:
    s = _settings(qwen_base_url="")
    assert build_qwen_cloud_status(s)["base_url_configured"] is False


# ---------------------------------------------------------------------------
# build_qwen_cloud_status — configured_model
# ---------------------------------------------------------------------------

def test_configured_model_uses_qwen_model_override() -> None:
    s = _settings(qwen_model="qwen-max", qwen_fast_model="qwen-turbo")
    assert build_qwen_cloud_status(s)["configured_model"] == "qwen-max"


def test_configured_model_falls_back_to_fast_model() -> None:
    s = _settings(qwen_model="", qwen_fast_model="qwen-turbo")
    assert build_qwen_cloud_status(s)["configured_model"] == "qwen-turbo"


def test_configured_model_whitespace_override_uses_fallback() -> None:
    s = _settings(qwen_model="   ", qwen_fast_model="qwen-turbo")
    assert build_qwen_cloud_status(s)["configured_model"] == "qwen-turbo"


# ---------------------------------------------------------------------------
# build_qwen_cloud_status — runtime_mode
# ---------------------------------------------------------------------------

def test_runtime_mode_mock() -> None:
    s = _settings(runtime_mode_label="MOCK_MODEL_MODE")
    assert build_qwen_cloud_status(s)["runtime_mode"] == "MOCK_MODEL_MODE"


def test_runtime_mode_real() -> None:
    s = _settings(runtime_mode_label="REAL_MODEL_MODE")
    assert build_qwen_cloud_status(s)["runtime_mode"] == "REAL_MODEL_MODE"


def test_runtime_mode_fallback() -> None:
    s = _settings(runtime_mode_label="FALLBACK_MODE")
    assert build_qwen_cloud_status(s)["runtime_mode"] == "FALLBACK_MODE"


# ---------------------------------------------------------------------------
# build_qwen_cloud_status — activation_note
# ---------------------------------------------------------------------------

def test_activation_note_mentions_aeonlogic_mode() -> None:
    status = build_qwen_cloud_status(_settings())
    assert "AEONLOGIC_MODE=real" in status["activation_note"]


def test_activation_note_mentions_qwen_api_key() -> None:
    status = build_qwen_cloud_status(_settings())
    assert "QWEN_API_KEY" in status["activation_note"]


def test_activation_note_constant_matches_status_note() -> None:
    status = build_qwen_cloud_status(_settings())
    assert status["activation_note"] == QWEN_ACTIVATION_NOTE


def test_activation_note_is_non_empty_string() -> None:
    assert isinstance(QWEN_ACTIVATION_NOTE, str) and len(QWEN_ACTIVATION_NOTE) > 10


# ---------------------------------------------------------------------------
# build_qwen_cloud_status — returns dict (type safety)
# ---------------------------------------------------------------------------

def test_status_returns_dict() -> None:
    assert isinstance(build_qwen_cloud_status(_settings()), dict)


def test_status_all_values_are_serialisable() -> None:
    """Every value should be a str or bool — safe for HTML rendering."""
    status = build_qwen_cloud_status(_settings(qwen_api_key="sk-testkey1234567890"))
    for k, v in status.items():
        assert isinstance(v, (str, bool)), f"Field {k!r} has non-str/bool type {type(v)}"
