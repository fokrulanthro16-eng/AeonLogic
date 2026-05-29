"""Phase 5A: Streamlit demo — import and pure-function unit tests.

No Streamlit runtime is needed.  All tests exercise the public API that
lives outside `_render()` and is safe to call from pytest.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from aeonlogic.app.streamlit_demo import (
    PAGE_TITLE,
    DEFAULT_GOAL,
    _build_summary,
    _collect_pipeline_events,
    _make_initial_state,
)
from aeonlogic.domain.finding import Verdict
from aeonlogic.domain.result import ExecutionStatus
from aeonlogic.domain.task import ModelTier


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

def test_page_title_is_non_empty_string() -> None:
    assert isinstance(PAGE_TITLE, str) and len(PAGE_TITLE) > 0


def test_default_goal_is_non_empty_string() -> None:
    assert isinstance(DEFAULT_GOAL, str) and len(DEFAULT_GOAL) > 0


def test_collect_pipeline_events_is_callable() -> None:
    assert callable(_collect_pipeline_events)


def test_build_summary_is_callable() -> None:
    assert callable(_build_summary)


# ---------------------------------------------------------------------------
# _make_initial_state
# ---------------------------------------------------------------------------

def test_make_initial_state_contains_goal() -> None:
    state = _make_initial_state("test goal", "ses-001")
    assert state["raw_goal"] == "test goal"


def test_make_initial_state_contains_session_id() -> None:
    state = _make_initial_state("goal", "ses-abc")
    assert state["session_id"] == "ses-abc"


def test_make_initial_state_generation_attempt_is_zero() -> None:
    state = _make_initial_state("goal", "sid")
    assert state["generation_attempt"] == 0


# ---------------------------------------------------------------------------
# _build_summary — empty / default
# ---------------------------------------------------------------------------

def test_build_summary_empty_events_returns_dict() -> None:
    result = _build_summary([])
    assert isinstance(result, dict)


def test_build_summary_empty_has_required_keys() -> None:
    result = _build_summary([])
    for key in ("risk_level", "model_name", "attempts", "repaired",
                "findings", "memory_lessons", "final_status",
                "total_findings", "execution_duration_ms", "execution_blocked"):
        assert key in result, f"Missing key: {key}"


def test_build_summary_empty_findings_list() -> None:
    assert _build_summary([])["findings"] == []


def test_build_summary_empty_repaired_is_false() -> None:
    assert _build_summary([])["repaired"] is False


def test_build_summary_empty_attempts_is_zero() -> None:
    assert _build_summary([])["attempts"] == 0


# ---------------------------------------------------------------------------
# _build_summary — dispatch event
# ---------------------------------------------------------------------------

def test_build_summary_extracts_risk_level() -> None:
    task = SimpleNamespace(risk_level="high", description="auth")
    events = [{"node": "dispatch", "update": {
        "active_task": task,
        "model_tier": ModelTier.FAST,
    }}]
    assert _build_summary(events)["risk_level"] == "HIGH"


def test_build_summary_risk_level_low() -> None:
    task = SimpleNamespace(risk_level="low", description="docs")
    events = [{"node": "dispatch", "update": {
        "active_task": task,
        "model_tier": ModelTier.FAST,
    }}]
    assert _build_summary(events)["risk_level"] == "LOW"


def test_build_summary_model_name_is_string() -> None:
    task = SimpleNamespace(risk_level="high", description="x")
    events = [{"node": "dispatch", "update": {
        "active_task": task,
        "model_tier": ModelTier.FAST,
    }}]
    assert isinstance(_build_summary(events)["model_name"], str)


def test_build_summary_no_task_gives_unknown_risk() -> None:
    events = [{"node": "dispatch", "update": {"active_task": None, "model_tier": ModelTier.FAST}}]
    assert _build_summary(events)["risk_level"] == "UNKNOWN"


# ---------------------------------------------------------------------------
# _build_summary — generate / repair detection
# ---------------------------------------------------------------------------

def test_build_summary_single_attempt_not_repaired() -> None:
    events = [{"node": "generate", "update": {"generation_attempt": 1}}]
    result = _build_summary(events)
    assert result["attempts"] == 1
    assert result["repaired"] is False


def test_build_summary_two_attempts_repaired() -> None:
    events = [
        {"node": "generate", "update": {"generation_attempt": 1}},
        {"node": "generate", "update": {"generation_attempt": 2}},
    ]
    result = _build_summary(events)
    assert result["attempts"] == 2
    assert result["repaired"] is True


def test_build_summary_max_attempt_tracked() -> None:
    events = [
        {"node": "generate", "update": {"generation_attempt": 1}},
        {"node": "generate", "update": {"generation_attempt": 2}},
        {"node": "generate", "update": {"generation_attempt": 3}},
    ]
    assert _build_summary(events)["attempts"] == 3


# ---------------------------------------------------------------------------
# _build_summary — critique / findings
# ---------------------------------------------------------------------------

def test_build_summary_rejected_verdict_collects_findings() -> None:
    finding = SimpleNamespace(
        severity="critical", title="No auth", evidence="plaintext", recommendation="use JWT"
    )
    events = [{"node": "critique", "update": {
        "critic_verdict": Verdict.REJECTED,
        "critic_findings": [finding],
    }}]
    result = _build_summary(events)
    assert len(result["findings"]) == 1
    assert result["total_findings"] == 1


def test_build_summary_approved_verdict_no_findings() -> None:
    events = [{"node": "critique", "update": {
        "critic_verdict": Verdict.APPROVED,
        "critic_findings": [],
    }}]
    result = _build_summary(events)
    assert result["findings"] == []
    assert result["total_findings"] == 0


def test_build_summary_finding_has_severity() -> None:
    finding = SimpleNamespace(severity="high", title="T", evidence="E", recommendation="")
    events = [{"node": "critique", "update": {
        "critic_verdict": Verdict.REJECTED,
        "critic_findings": [finding],
    }}]
    f = _build_summary(events)["findings"][0]
    assert f["severity"] == "high"
    assert f["title"] == "T"


def test_build_summary_multiple_findings_counted() -> None:
    findings = [
        SimpleNamespace(severity="critical", title=f"F{i}", evidence="", recommendation="")
        for i in range(5)
    ]
    events = [{"node": "critique", "update": {
        "critic_verdict": Verdict.REJECTED,
        "critic_findings": findings,
    }}]
    assert _build_summary(events)["total_findings"] == 5


# ---------------------------------------------------------------------------
# _build_summary — execute
# ---------------------------------------------------------------------------

def test_build_summary_blocked_execution() -> None:
    events = [{"node": "execute", "update": {
        "execution_status": ExecutionStatus.FAILURE,
        "execution_result": None,
    }}]
    assert _build_summary(events)["execution_blocked"] is True


def test_build_summary_successful_execution_not_blocked() -> None:
    events = [{"node": "execute", "update": {
        "execution_status": ExecutionStatus.SUCCESS,
        "execution_result": None,
    }}]
    assert _build_summary(events)["execution_blocked"] is False


# ---------------------------------------------------------------------------
# _build_summary — synthesize / final status
# ---------------------------------------------------------------------------

def test_build_summary_final_status_from_synthesize() -> None:
    from aeonlogic.domain.task import CycleStatus
    events = [{"node": "synthesize", "update": {
        "status": CycleStatus.SUCCESS,
        "lessons_written": [],
    }}]
    assert "SUCCESS" in _build_summary(events)["final_status"]


def test_build_summary_memory_lessons_extracted() -> None:
    lessons = [
        {"type": "failure-lesson", "id": "abc", "content": "null pointer"},
        {"type": "success-lesson", "id": "def", "content": "bcrypt used"},
    ]
    events = [{"node": "synthesize", "update": {"lessons_written": lessons}}]
    result = _build_summary(events)
    assert len(result["memory_lessons"]) == 2
