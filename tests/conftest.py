"""Shared fixtures for the AeonLogic test suite."""
from __future__ import annotations

from collections.abc import Generator

import pytest

from aeonlogic.domain.task import CycleStatus, ModelTier
from aeonlogic.graph.state import AeonState
from aeonlogic.utils.ids import new_ulid


@pytest.fixture(autouse=True)
def _clear_memory_store() -> Generator[None, None, None]:
    """Reset the module-level in-process store before and after every test."""
    from aeonlogic.agents.memory_synthesizer import _store

    _store.clear()
    yield
    _store.clear()


@pytest.fixture
def make_state():
    """
    Factory fixture: returns (AeonState, graph_config) for a given goal.
    Produces a fresh ULID session ID on every call.
    """

    def _factory(goal: str = "Build a secure API authentication module") -> tuple[AeonState, dict]:
        sid = new_ulid()
        state: AeonState = {
            "session_id":         sid,
            "cycle_id":           "",
            "generation_attempt": 0,
            "raw_goal":           goal,
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
        config = {"configurable": {"thread_id": sid}}
        return state, config

    return _factory
