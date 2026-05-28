from __future__ import annotations

from langgraph.graph import END

from aeonlogic.domain.result import ExecutionStatus
from aeonlogic.domain.task import CycleStatus
from aeonlogic.graph.state import AeonState

MAX_RECURSION_DEPTH: int = 10


def after_dispatch(state: AeonState) -> str:
    if state.get("status") == CycleStatus.FAILED:  # type: ignore[call-overload]
        return END  # type: ignore[return-value]
    return "generate"


def after_generate(state: AeonState) -> str:
    if state.get("status") == CycleStatus.FAILED:  # type: ignore[call-overload]
        return "synthesize"
    return "critique"


def after_critique(state: AeonState) -> str:
    # Executor is the final execution gate — always route through it.
    # The Critic only reports; the Executor decides block or proceed.
    if state.get("status") == CycleStatus.FAILED:  # type: ignore[call-overload]
        return "synthesize"
    return "execute"


def after_execute(state: AeonState) -> str:
    exec_status = state.get("execution_status")  # type: ignore[call-overload]
    if exec_status == ExecutionStatus.FAILURE:
        attempt: int = state.get("generation_attempt") or 0  # type: ignore[call-overload]
        if attempt >= MAX_RECURSION_DEPTH:
            return "synthesize"
        return "generate"
    # SUCCESS or TIMEOUT -> finalise
    return "synthesize"


def after_synthesize(state: AeonState) -> str:
    return END  # type: ignore[return-value]
