from __future__ import annotations

from typing import Any, TypedDict

from aeonlogic.domain.artifact import Artifact
from aeonlogic.domain.finding import Finding, Verdict
from aeonlogic.domain.result import ExecutionStatus, Result
from aeonlogic.domain.task import CycleStatus, ModelTier, Task


class AeonState(TypedDict):
    # ── Identity ────────────────────────────────────────────────────────────
    session_id: str
    cycle_id: str
    generation_attempt: int

    # ── Input ───────────────────────────────────────────────────────────────
    raw_goal: str
    tasks: list[Task]
    active_task: Task | None

    # ── Routing ─────────────────────────────────────────────────────────────
    model_tier: ModelTier

    # ── Memory ──────────────────────────────────────────────────────────────
    memory_context: dict[str, Any]
    memory_write_ids: list[str]
    lessons_written: list[dict[str, str]]

    # ── Generation ──────────────────────────────────────────────────────────
    candidate_artifact: Artifact | None

    # ── Critique ────────────────────────────────────────────────────────────
    critic_verdict: Verdict | None
    critic_findings: list[Finding]

    # ── Execution ───────────────────────────────────────────────────────────
    execution_result: Result | None
    execution_status: ExecutionStatus | None

    # ── Control flow ────────────────────────────────────────────────────────
    status: CycleStatus
    error: str | None

    # ── Traces (for audit log) ───────────────────────────────────────────────
    dispatcher_trace: str
    generator_trace: str
    critic_trace: str
    executor_trace: str
    synthesizer_trace: str
