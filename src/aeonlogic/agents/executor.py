from __future__ import annotations

import re
from typing import Any

from aeonlogic.agents.base import BaseAgent
from aeonlogic.domain.finding import FindingSeverity
from aeonlogic.domain.result import ExecutionStatus, Result
from aeonlogic.graph.state import AeonState

# Severity levels that cause an immediate execution block
_BLOCKING_SEVERITIES: frozenset[FindingSeverity] = frozenset(
    [FindingSeverity.CRITICAL, FindingSeverity.HIGH]
)

# Last-resort pattern scan: catches anything that slipped past the Critic
_EMERGENCY_PATTERNS: list[tuple[str, str]] = [
    (
        r"(SECRET_KEY|API_KEY|SECRET)\s*=\s*['\"][^'\"]{3,}['\"]",
        "hardcoded secret in artifact",
    ),
    (
        r"(username|password)\s*==\s*['\"][^'\"]+['\"]",
        "hardcoded credential comparison in artifact",
    ),
]


class ExecutorAgent(BaseAgent):
    name = "executor"

    def __call__(self, state: AeonState) -> dict[str, Any]:
        active_task = state["active_task"]
        if active_task is None:
            raise ValueError("ExecutorAgent: no active_task in state")
        artifact = state["candidate_artifact"]
        if artifact is None:
            raise ValueError("ExecutorAgent: no candidate_artifact in state")

        # ── Primary gate: block on unresolved CRITICAL / HIGH critic findings ──
        critic_findings = state.get("critic_findings") or []  # type: ignore[call-overload]
        blocking = [f for f in critic_findings if f.severity in _BLOCKING_SEVERITIES]

        if blocking:
            top = blocking[0]
            result = Result(
                task_id=active_task.id,
                artifact_id=artifact.id,
                status=ExecutionStatus.FAILURE,
                summary=(
                    f"Execution blocked: {len(blocking)} unresolved "
                    f"critical/high security finding(s)."
                ),
                stderr=f"[{top.severity.upper()}] {top.title} | {top.evidence[:80]}",
                duration_ms=0,
            )
            return {
                "execution_result": result,
                "execution_status": ExecutionStatus.FAILURE,
                "executor_trace": (
                    f"BLOCKED -> {len(blocking)} critical/high finding(s). "
                    f"Top: {top.title}"
                ),
            }

        # ── Secondary gate: emergency pattern scan (defense in depth) ──────────
        for pattern, reason in _EMERGENCY_PATTERNS:
            if re.search(pattern, artifact.content, re.IGNORECASE):
                result = Result(
                    task_id=active_task.id,
                    artifact_id=artifact.id,
                    status=ExecutionStatus.FAILURE,
                    summary=f"Execution blocked by emergency scan: {reason}.",
                    stderr=f"SEC-EMERGENCY: {reason}",
                    duration_ms=0,
                )
                return {
                    "execution_result": result,
                    "execution_status": ExecutionStatus.FAILURE,
                    "executor_trace": f"EMERGENCY BLOCK -> {reason}",
                }

        # ── Artifact is clean: accept ─────────────────────────────────────────
        result = Result(
            task_id=active_task.id,
            artifact_id=artifact.id,
            status=ExecutionStatus.SUCCESS,
            summary="Artifact validated and accepted. All security checks passed.",
            stdout="[EXECUTOR] Artifact processed successfully.",
            duration_ms=42,
        )
        return {
            "execution_result": result,
            "execution_status": ExecutionStatus.SUCCESS,
            "executor_trace": (
                f"SUCCESS -> artifact {artifact.id[:8]}... "
                f"cleared all checks in {result.duration_ms} ms"
            ),
        }
