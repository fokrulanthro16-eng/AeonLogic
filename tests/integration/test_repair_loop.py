"""Integration tests: full LangGraph repair loop for the auth demo task."""
from __future__ import annotations

from typing import Any

import pytest

from aeonlogic.domain.result import ExecutionStatus
from aeonlogic.domain.task import CycleStatus
from aeonlogic.graph.builder import build_graph


# ── Module-scoped fixture: run the graph once, share results ──────────────────

@pytest.fixture(scope="module")
def auth_run() -> dict[str, Any]:
    """
    Runs the full LangGraph pipeline for the auth demo goal once per module.
    Returns a dict with: nodes, exec_statuses, final_state.
    """
    from aeonlogic.domain.task import ModelTier
    from aeonlogic.graph.state import AeonState
    from aeonlogic.utils.ids import new_ulid

    graph = build_graph()
    sid = new_ulid()
    config = {"configurable": {"thread_id": sid}}
    initial: AeonState = {
        "session_id":         sid,
        "cycle_id":           "",
        "generation_attempt": 0,
        "raw_goal":           "Build a secure API authentication module",
        "tasks":              [],
        "active_task":        None,
        "model_tier":         ModelTier.FAST,
        "memory_context":     {},
        "memory_write_ids":   [],
        "lessons_written":    [],
        "candidate_artifact": None,
        "critic_verdict":     None,
        "critic_findings":    [],
        "execution_result":   None,
        "execution_status":   None,
        "status":             CycleStatus.RUNNING,
        "error":              None,
        "dispatcher_trace":   "",
        "generator_trace":    "",
        "critic_trace":       "",
        "executor_trace":     "",
        "synthesizer_trace":  "",
    }

    nodes: list[str] = []
    exec_statuses: list[str] = []

    for step in graph.stream(initial, config=config, stream_mode="updates"):
        for node, update in step.items():
            nodes.append(node)
            if node == "execute":
                exec_statuses.append(str(update.get("execution_status", "")))

    final = graph.get_state(config).values
    return {"nodes": nodes, "exec_statuses": exec_statuses, "final": final}


# ── Node sequence (enforced by graph edges, not CLI) ─────────────────────────

def test_exact_node_sequence(auth_run: dict) -> None:
    assert auth_run["nodes"] == [
        "dispatch",
        "generate",   # attempt 1 — weak artifact
        "critique",   # finds 5 security issues
        "execute",    # BLOCKED — primary gate fires
        "generate",   # attempt 2 — repair
        "critique",   # 0 findings
        "execute",    # SUCCESS
        "synthesize",
    ]


def test_execute_runs_twice(auth_run: dict) -> None:
    assert auth_run["nodes"].count("execute") == 2


def test_generate_runs_twice(auth_run: dict) -> None:
    assert auth_run["nodes"].count("generate") == 2


def test_critique_runs_twice(auth_run: dict) -> None:
    assert auth_run["nodes"].count("critique") == 2


# ── Attempt outcomes ──────────────────────────────────────────────────────────

def test_attempt_1_execute_is_blocked(auth_run: dict) -> None:
    assert auth_run["exec_statuses"][0] == ExecutionStatus.FAILURE


def test_attempt_2_execute_succeeds(auth_run: dict) -> None:
    assert auth_run["exec_statuses"][1] == ExecutionStatus.SUCCESS


# ── Final state ───────────────────────────────────────────────────────────────

def test_final_status_is_success(auth_run: dict) -> None:
    assert auth_run["final"]["status"] == CycleStatus.SUCCESS


def test_final_generation_attempt_is_2(auth_run: dict) -> None:
    assert auth_run["final"]["generation_attempt"] == 2


def test_final_critic_findings_are_empty(auth_run: dict) -> None:
    assert auth_run["final"]["critic_findings"] == []


def test_final_artifact_is_present(auth_run: dict) -> None:
    assert auth_run["final"]["candidate_artifact"] is not None


def test_final_execution_status_is_success(auth_run: dict) -> None:
    assert auth_run["final"]["execution_status"] == ExecutionStatus.SUCCESS


# ── Memory lessons ────────────────────────────────────────────────────────────

def test_two_lessons_written(auth_run: dict) -> None:
    assert len(auth_run["final"]["lessons_written"]) == 2


def test_failure_lesson_is_written(auth_run: dict) -> None:
    types = [l["type"] for l in auth_run["final"]["lessons_written"]]
    assert "failure-lesson" in types


def test_success_lesson_is_written(auth_run: dict) -> None:
    types = [l["type"] for l in auth_run["final"]["lessons_written"]]
    assert "success-lesson" in types


def test_all_lessons_have_content(auth_run: dict) -> None:
    for lesson in auth_run["final"]["lessons_written"]:
        assert lesson["content"].strip()
