"""Phase 5A/5B/5C: Streamlit demo — import and pure-function unit tests.

No Streamlit runtime is needed.  All tests exercise the public API that
lives outside `_render()` and is safe to call from pytest.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from aeonlogic.app.streamlit_demo import (
    PAGE_TITLE,
    PAGE_SUBTITLE,
    DEFAULT_GOAL,
    DEMO_TASKS,
    _build_summary,
    _build_timeline_stages,
    _collect_pipeline_events,
    _make_initial_state,
    build_demo_summary_text,
    format_download_filename,
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


# ---------------------------------------------------------------------------
# PAGE_SUBTITLE constant (Phase 5B)
# ---------------------------------------------------------------------------

def test_page_subtitle_constant_exists() -> None:
    assert isinstance(PAGE_SUBTITLE, str) and len(PAGE_SUBTITLE) > 0


def test_page_subtitle_contains_self_healing() -> None:
    assert "Self-Healing" in PAGE_SUBTITLE or "self-healing" in PAGE_SUBTITLE.lower()


def test_page_subtitle_contains_engine() -> None:
    assert "Engine" in PAGE_SUBTITLE or "engine" in PAGE_SUBTITLE.lower()


# ---------------------------------------------------------------------------
# _build_timeline_stages (Phase 5B)
# ---------------------------------------------------------------------------

def test_build_timeline_stages_is_callable() -> None:
    assert callable(_build_timeline_stages)


def test_build_timeline_stages_empty_events_returns_list() -> None:
    result = _build_timeline_stages([])
    assert isinstance(result, list)


def test_build_timeline_stages_empty_events_empty_list() -> None:
    assert _build_timeline_stages([]) == []


def test_build_timeline_stages_includes_dispatch() -> None:
    task = SimpleNamespace(risk_level="high", description="auth")
    events = [{"node": "dispatch", "update": {"active_task": task, "model_tier": "FAST"}}]
    assert "DISPATCH" in _build_timeline_stages(events)


def test_build_timeline_stages_includes_generate() -> None:
    events = [{"node": "generate", "update": {"generation_attempt": 1}}]
    assert "GENERATE" in _build_timeline_stages(events)


def test_build_timeline_stages_includes_critic() -> None:
    events = [{"node": "critique", "update": {"critic_verdict": None, "critic_findings": []}}]
    assert "CRITIC" in _build_timeline_stages(events)


def test_build_timeline_stages_includes_execute() -> None:
    events = [{"node": "execute", "update": {"execution_status": None}}]
    assert "EXECUTE" in _build_timeline_stages(events)


def test_build_timeline_stages_includes_memory_from_synthesize() -> None:
    events = [{"node": "synthesize", "update": {"lessons_written": []}}]
    assert "MEMORY" in _build_timeline_stages(events)


def test_build_timeline_stages_includes_final_when_memory_present() -> None:
    events = [{"node": "synthesize", "update": {"lessons_written": []}}]
    assert "FINAL" in _build_timeline_stages(events)


def test_build_timeline_stages_repair_when_two_attempts() -> None:
    events = [
        {"node": "generate", "update": {"generation_attempt": 1}},
        {"node": "generate", "update": {"generation_attempt": 2}},
    ]
    assert "REPAIR" in _build_timeline_stages(events)


def test_build_timeline_stages_no_repair_for_single_attempt() -> None:
    events = [{"node": "generate", "update": {"generation_attempt": 1}}]
    assert "REPAIR" not in _build_timeline_stages(events)


def test_build_timeline_stages_order_preserved() -> None:
    events = [
        {"node": "dispatch",  "update": {}},
        {"node": "generate",  "update": {"generation_attempt": 1}},
        {"node": "critique",  "update": {}},
        {"node": "execute",   "update": {}},
        {"node": "synthesize","update": {"lessons_written": []}},
    ]
    stages = _build_timeline_stages(events)
    expected_order = ["DISPATCH", "GENERATE", "CRITIC", "EXECUTE", "MEMORY", "FINAL"]
    indices = [stages.index(s) for s in expected_order if s in stages]
    assert indices == sorted(indices)


# ---------------------------------------------------------------------------
# build_demo_summary_text (Phase 5B)
# ---------------------------------------------------------------------------

def _sample_summary() -> dict[str, Any]:
    return {
        "model_name":            "qwen-turbo",
        "risk_level":            "HIGH",
        "attempts":              2,
        "repaired":              True,
        "findings":              [],
        "total_findings":        5,
        "execution_blocked":     True,
        "execution_duration_ms": 120,
        "memory_lessons": [
            {"type": "failure-lesson", "id": "a", "content": "null pointer"},
            {"type": "success-lesson",  "id": "b", "content": "bcrypt"},
        ],
        "final_status": "SUCCESS",
    }


def test_build_demo_summary_text_is_callable() -> None:
    assert callable(build_demo_summary_text)


def test_build_demo_summary_text_returns_string() -> None:
    result = build_demo_summary_text("ses-001", "MOCK_MODEL_MODE", _sample_summary())
    assert isinstance(result, str)


def test_build_demo_summary_text_contains_session_id() -> None:
    result = build_demo_summary_text("ses-XYZ", "MOCK_MODEL_MODE", _sample_summary())
    assert "ses-XYZ" in result


def test_build_demo_summary_text_contains_runtime_mode() -> None:
    result = build_demo_summary_text("sid", "MOCK_MODEL_MODE", _sample_summary())
    assert "MOCK_MODEL_MODE" in result


def test_build_demo_summary_text_contains_final_status() -> None:
    result = build_demo_summary_text("sid", "MOCK", _sample_summary())
    assert "SUCCESS" in result


def test_build_demo_summary_text_contains_model_name() -> None:
    result = build_demo_summary_text("sid", "MOCK", _sample_summary())
    assert "qwen-turbo" in result


def test_build_demo_summary_text_repair_note_when_repaired() -> None:
    result = build_demo_summary_text("sid", "MOCK", _sample_summary())
    assert "self-healing" in result.lower() or "repaired" in result.lower() or "repair" in result.lower()


def test_build_demo_summary_text_no_repair_note_when_not_repaired() -> None:
    s = _sample_summary()
    s["repaired"]  = False
    s["attempts"]  = 1
    result = build_demo_summary_text("sid", "MOCK", s)
    assert "first-pass" in result.lower() or "first pass" in result.lower()


def test_build_demo_summary_text_lesson_counts() -> None:
    result = build_demo_summary_text("sid", "MOCK", _sample_summary())
    # 2 lessons written
    assert "2" in result


def test_build_demo_summary_text_risk_level() -> None:
    result = build_demo_summary_text("sid", "MOCK", _sample_summary())
    assert "HIGH" in result


# ---------------------------------------------------------------------------
# DEMO_TASKS constant (Phase 5C)
# ---------------------------------------------------------------------------

def test_demo_tasks_is_list() -> None:
    assert isinstance(DEMO_TASKS, list)


def test_demo_tasks_has_three_items() -> None:
    assert len(DEMO_TASKS) == 3


def test_demo_tasks_each_has_required_keys() -> None:
    for task in DEMO_TASKS:
        assert "label"       in task, f"Missing 'label' in {task}"
        assert "goal"        in task, f"Missing 'goal' in {task}"
        assert "description" in task, f"Missing 'description' in {task}"


def test_demo_tasks_labels_are_non_empty() -> None:
    for task in DEMO_TASKS:
        assert len(task["label"].strip()) > 0


def test_demo_tasks_goals_are_non_empty() -> None:
    for task in DEMO_TASKS:
        assert len(task["goal"].strip()) > 0


def test_demo_tasks_security_auth_goal_matches_default() -> None:
    security_task = DEMO_TASKS[0]
    assert security_task["goal"] == DEFAULT_GOAL


def test_demo_tasks_input_validation_goal_contains_validation() -> None:
    val_task = DEMO_TASKS[1]
    assert "validation" in val_task["goal"].lower() or "sanitiz" in val_task["goal"].lower()


def test_demo_tasks_rate_limiting_goal_contains_rate() -> None:
    rate_task = DEMO_TASKS[2]
    assert "rate" in rate_task["goal"].lower()


def test_demo_tasks_all_goals_are_distinct() -> None:
    goals = [t["goal"] for t in DEMO_TASKS]
    assert len(set(goals)) == len(goals), "Duplicate goals in DEMO_TASKS"


# ---------------------------------------------------------------------------
# format_download_filename (Phase 5C)
# ---------------------------------------------------------------------------

def test_format_download_filename_is_callable() -> None:
    assert callable(format_download_filename)


def test_format_download_filename_returns_string() -> None:
    result = format_download_filename("ABCDEF12", "SUCCESS")
    assert isinstance(result, str)


def test_format_download_filename_ends_with_txt() -> None:
    assert format_download_filename("sid", "SUCCESS").endswith(".txt")


def test_format_download_filename_success_slug() -> None:
    name = format_download_filename("abcdef12", "SUCCESS")
    assert "success" in name


def test_format_download_filename_failed_slug_for_non_success() -> None:
    name = format_download_filename("abcdef12", "FAILED")
    assert "failed" in name


def test_format_download_filename_unknown_status_is_failed() -> None:
    name = format_download_filename("abcdef12", "UNKNOWN")
    assert "failed" in name


def test_format_download_filename_contains_session_prefix() -> None:
    name = format_download_filename("ABCDEF12XYZ", "SUCCESS")
    # First 8 chars of session_id (lowercased) appear in filename
    assert "abcdef12" in name


def test_format_download_filename_short_session_id() -> None:
    name = format_download_filename("AB", "SUCCESS")
    assert "ab" in name
    assert name.endswith(".txt")


def test_format_download_filename_starts_with_aeonlogic() -> None:
    name = format_download_filename("sess", "SUCCESS")
    assert name.startswith("aeonlogic_demo_")
