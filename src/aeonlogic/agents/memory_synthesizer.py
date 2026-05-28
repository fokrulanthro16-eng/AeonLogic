from __future__ import annotations

from typing import Any

from aeonlogic.agents.base import BaseAgent
from aeonlogic.domain.result import ExecutionStatus
from aeonlogic.domain.task import CycleStatus, ModelTier
from aeonlogic.graph.state import AeonState
from aeonlogic.models.budgets import get_budget
from aeonlogic.models.prompts import synthesize_prompt
from aeonlogic.models.qwen_client import get_client
from aeonlogic.utils.ids import new_ulid

# ── In-process lesson store ───────────────────────────────────────────────────
# Persists for the lifetime of the process; shared across all sessions.

class _Lesson:
    __slots__ = ("id", "lesson_type", "content", "tags")

    def __init__(self, lesson_id: str, lesson_type: str, content: str, tags: str) -> None:
        self.id = lesson_id
        self.lesson_type = lesson_type
        self.content = content
        self.tags = tags


_store: list[_Lesson] = []


def get_all_lessons() -> list[_Lesson]:
    return list(_store)


def _write(lesson_type: str, content: str, tags: str = "") -> _Lesson:
    lesson = _Lesson(
        lesson_id=new_ulid(),
        lesson_type=lesson_type,
        content=content,
        tags=tags,
    )
    _store.append(lesson)
    return lesson


# ── Agent ─────────────────────────────────────────────────────────────────────

class MemorySynthesizerAgent(BaseAgent):
    name = "memory_synthesizer"

    def __call__(self, state: AeonState) -> dict[str, Any]:
        active_task = state["active_task"]
        if active_task is None:
            raise ValueError("MemorySynthesizerAgent: no active_task in state")

        client = get_client()
        budget = get_budget(ModelTier.FAST)
        result = state.get("execution_result")  # type: ignore[call-overload]
        exec_status = state.get("execution_status")  # type: ignore[call-overload]
        generation_attempt: int = state.get("generation_attempt") or 0  # type: ignore[call-overload]

        client.complete(
            budget=budget,
            prompt=synthesize_prompt(
                task_description=active_task.description,
                result_summary=result.summary if result else "No result.",
            ),
        )

        written: list[dict[str, str]] = []

        # Write a failure/repair lesson when the cycle required at least one repair
        if generation_attempt > 1:
            lesson = _write(
                lesson_type="failure-lesson",
                content=(
                    f"Task '{active_task.description[:60]}' required "
                    f"{generation_attempt - 1} repair cycle(s). "
                    "Security issues were detected and corrected."
                ),
                tags="security,repair",
            )
            written.append({"id": lesson.id, "type": lesson.lesson_type, "content": lesson.content})

        # Always write a success (or failure) outcome lesson
        outcome = result.summary if result else "No execution result."
        lesson = _write(
            lesson_type="success-lesson" if exec_status == ExecutionStatus.SUCCESS else "failure-lesson",
            content=(
                f"Task '{active_task.description[:60]}' -> "
                f"{'SUCCESS' if exec_status == ExecutionStatus.SUCCESS else 'FAILED'} "
                f"after {generation_attempt} attempt(s). {outcome}"
            ),
            tags="security,authentication,outcome",
        )
        written.append({"id": lesson.id, "type": lesson.lesson_type, "content": lesson.content})

        cycle_status = (
            CycleStatus.SUCCESS
            if exec_status == ExecutionStatus.SUCCESS
            else CycleStatus.FAILED
        )

        trace_lines = [f"Wrote {len(written)} lessons to in-process store:"]
        for entry in written:
            trace_lines.append(
                f"  [{entry['id'][:16]}...] {entry['type']}: {entry['content'][:72]}"
            )

        return {
            "memory_write_ids": [e["id"] for e in written],
            "lessons_written": written,
            "memory_context": {"lessons": [e["content"] for e in written]},
            "status": cycle_status,
            "synthesizer_trace": "\n".join(trace_lines),
        }
