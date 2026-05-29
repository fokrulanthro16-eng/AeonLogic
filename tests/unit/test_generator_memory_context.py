"""Phase 4C: memory-aware Generator context — unit tests."""
from __future__ import annotations

from typing import Any

import pytest

from aeonlogic.agents.generator import GeneratorAgent
from aeonlogic.domain.task import CycleStatus, ModelTier, Task
from aeonlogic.graph.state import AeonState
from aeonlogic.memory.retrieval import summarize_lessons
from aeonlogic.memory.schemas import Lesson
from aeonlogic.utils.ids import new_ulid


# ---------------------------------------------------------------------------
# State builder
# ---------------------------------------------------------------------------

def _make_state(
    memory_context: dict[str, Any] | None = None,
    critic_findings: list | None = None,
) -> AeonState:
    task = Task(description="Build a secure authentication module")
    return {
        "session_id":         new_ulid(),
        "cycle_id":           "",
        "generation_attempt": 0,
        "raw_goal":           "auth",
        "tasks":              [task],
        "active_task":        task,
        "model_tier":         ModelTier.FAST,
        "memory_context":     memory_context if memory_context is not None else {},
        "memory_write_ids":   [],
        "lessons_written":    [],
        "candidate_artifact": None,
        "critic_verdict":     None,
        "critic_findings":    critic_findings or [],
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


# ---------------------------------------------------------------------------
# Mock client — records prompts, returns stable content
# ---------------------------------------------------------------------------

class _CapturingClient:
    def __init__(self, response: str = "generated content") -> None:
        self._response = response
        self.prompts: list[str] = []

    def complete(self, budget: object, prompt: str) -> str:
        self.prompts.append(prompt)
        return self._response


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> _CapturingClient:
    cap = _CapturingClient()
    monkeypatch.setattr("aeonlogic.agents.generator.get_client", lambda: cap)
    return cap


# ---------------------------------------------------------------------------
# summarize_lessons (unit)
# ---------------------------------------------------------------------------

def test_summarize_empty_returns_empty_string() -> None:
    assert summarize_lessons([]) == ""


def test_summarize_includes_header() -> None:
    result = summarize_lessons([Lesson(content="use bcrypt", source="success")])
    assert result.startswith("Relevant past lessons:")


def test_summarize_includes_content_and_source() -> None:
    result = summarize_lessons([Lesson(content="use bcrypt", source="success")])
    assert "use bcrypt" in result
    assert "[success]" in result


def test_summarize_caps_at_max_lessons() -> None:
    lessons = [Lesson(content=f"lesson {i}", source="agent") for i in range(10)]
    result = summarize_lessons(lessons, max_lessons=3)
    assert "lesson 2" in result
    assert "lesson 3" not in result


def test_summarize_default_cap_is_five() -> None:
    lessons = [Lesson(content=f"lesson {i}", source="agent") for i in range(10)]
    result = summarize_lessons(lessons)
    assert "lesson 4" in result
    assert "lesson 5" not in result


# ---------------------------------------------------------------------------
# Generator with empty memory context — zero behavioral change
# ---------------------------------------------------------------------------

def test_generator_runs_with_empty_memory_context(client: _CapturingClient) -> None:
    result = GeneratorAgent()(_make_state(memory_context={}))
    assert result["candidate_artifact"] is not None
    assert result["generation_attempt"] == 1


def test_empty_memory_context_no_hint_in_prompt(client: _CapturingClient) -> None:
    GeneratorAgent()(_make_state(memory_context={}))
    assert "Relevant past lessons" not in client.prompts[0]


def test_empty_lessons_list_no_hint_in_prompt(client: _CapturingClient) -> None:
    GeneratorAgent()(_make_state(memory_context={"lessons": []}))
    assert "Relevant past lessons" not in client.prompts[0]


def test_empty_memory_context_no_trace_annotation(client: _CapturingClient) -> None:
    result = GeneratorAgent()(_make_state(memory_context={}))
    assert "[memory:" not in result["generator_trace"]


def test_identical_prompt_across_two_empty_context_calls(client: _CapturingClient) -> None:
    """Empty memory_context must produce the same prompt each time — no side effects."""
    GeneratorAgent()(_make_state(memory_context={}))
    GeneratorAgent()(_make_state(memory_context={}))
    assert client.prompts[0] == client.prompts[1]


def test_missing_memory_context_key_does_not_crash(client: _CapturingClient) -> None:
    """State with no memory_context key at all must not crash."""
    state = _make_state()
    state.pop("memory_context", None)  # type: ignore[misc]
    result = GeneratorAgent()(state)
    assert result["candidate_artifact"] is not None


# ---------------------------------------------------------------------------
# Generator with lessons — memory hint injected
# ---------------------------------------------------------------------------

def test_memory_hint_present_when_lessons_given(client: _CapturingClient) -> None:
    lessons = [Lesson(content="always validate JWT signatures", source="failure")]
    GeneratorAgent()(_make_state(memory_context={"lessons": lessons}))
    assert "Relevant past lessons" in client.prompts[0]


def test_memory_hint_contains_lesson_content(client: _CapturingClient) -> None:
    lessons = [Lesson(content="always validate JWT signatures before trusting claims", source="failure")]
    GeneratorAgent()(_make_state(memory_context={"lessons": lessons}))
    assert "always validate JWT signatures before trusting claims" in client.prompts[0]


def test_memory_hint_contains_source_label(client: _CapturingClient) -> None:
    lessons = [Lesson(content="use bcrypt for password hashing", source="success")]
    GeneratorAgent()(_make_state(memory_context={"lessons": lessons}))
    assert "[success]" in client.prompts[0]


def test_memory_hint_prepended_before_base_prompt(client: _CapturingClient) -> None:
    """Hint must appear before the task description in the final prompt."""
    lessons = [Lesson(content="sanitize all inputs", source="success")]
    GeneratorAgent()(_make_state(memory_context={"lessons": lessons}))
    prompt = client.prompts[0]
    assert prompt.startswith("Relevant past lessons:")


def test_multiple_lessons_all_appear_in_prompt(client: _CapturingClient) -> None:
    lessons = [
        Lesson(content="use HTTPS for all endpoints", source="success"),
        Lesson(content="avoid storing plaintext passwords", source="failure"),
    ]
    GeneratorAgent()(_make_state(memory_context={"lessons": lessons}))
    prompt = client.prompts[0]
    assert "use HTTPS for all endpoints" in prompt
    assert "avoid storing plaintext passwords" in prompt


def test_generator_trace_annotated_with_lesson_count(client: _CapturingClient) -> None:
    lessons = [Lesson(content="lesson", source="agent") for _ in range(3)]
    result = GeneratorAgent()(_make_state(memory_context={"lessons": lessons}))
    assert "[memory: 3 lesson(s)]" in result["generator_trace"]


def test_generator_trace_not_annotated_when_empty(client: _CapturingClient) -> None:
    result = GeneratorAgent()(_make_state(memory_context={}))
    assert "[memory:" not in result["generator_trace"]


# ---------------------------------------------------------------------------
# Repair-loop determinism invariant
# ---------------------------------------------------------------------------

def test_attempt_counter_increments_independently_of_memory(client: _CapturingClient) -> None:
    agent = GeneratorAgent()
    state = _make_state(memory_context={})
    r1 = agent(state)
    assert r1["generation_attempt"] == 1
    state["generation_attempt"] = 1
    r2 = agent(state)
    assert r2["generation_attempt"] == 2


def test_memory_context_does_not_affect_attempt_counter(client: _CapturingClient) -> None:
    lessons = [Lesson(content="past lesson", source="success")]
    agent = GeneratorAgent()
    state_mem = _make_state(memory_context={"lessons": lessons})
    state_empty = _make_state(memory_context={})
    assert agent(state_mem)["generation_attempt"] == agent(state_empty)["generation_attempt"]


def test_critic_findings_forwarded_independently_of_memory(client: _CapturingClient) -> None:
    """Findings in state must reach the prompt regardless of memory context."""
    from aeonlogic.domain.finding import Finding
    finding = Finding(
        artifact_id=new_ulid(),
        severity="critical",
        category="security",
        title="No input validation",
        description="User input not validated before use",
        evidence="User input passed directly to SQL",
    )
    lessons = [Lesson(content="validate inputs", source="success")]
    GeneratorAgent()(_make_state(
        memory_context={"lessons": lessons},
        critic_findings=[finding],
    ))
    prompt = client.prompts[0]
    assert "No input validation" in prompt
