from __future__ import annotations

from typing import Any

from aeonlogic.agents.base import BaseAgent
from aeonlogic.domain.task import CycleStatus, ModelTier, RiskLevel, Task
from aeonlogic.graph.state import AeonState
from aeonlogic.models.budgets import get_budget
from aeonlogic.models.prompts import dispatch_prompt
from aeonlogic.models.qwen_client import get_client
from aeonlogic.models.router import route_model
from aeonlogic.utils.ids import new_ulid

# Keywords that elevate a task to HIGH risk → STRONG model tier
_HIGH_RISK_KEYWORDS: frozenset[str] = frozenset(
    [
        "auth", "authentication", "authorize", "authorization",
        "security", "secure", "secret", "credential", "credentials",
        "password", "token", "jwt", "oauth", "api key", "access control",
        "privilege", "permission", "encrypt", "encryption",
    ]
)


def _classify_risk(raw_goal: str) -> RiskLevel:
    lower = raw_goal.lower()
    if any(kw in lower for kw in _HIGH_RISK_KEYWORDS):
        return RiskLevel.HIGH
    return RiskLevel.MEDIUM


class DispatcherAgent(BaseAgent):
    name = "dispatcher"

    def __call__(self, state: AeonState) -> dict[str, Any]:
        raw_goal = state["raw_goal"]
        client = get_client()

        risk_level = _classify_risk(raw_goal)
        model_tier = route_model(risk_level)
        budget = get_budget(model_tier)

        response = client.complete(budget=budget, prompt=dispatch_prompt(raw_goal))
        task = Task(description=raw_goal, risk_level=risk_level)

        return {
            "tasks": [task],
            "active_task": task,
            "model_tier": model_tier,
            "cycle_id": new_ulid(),
            "generation_attempt": 0,
            "status": CycleStatus.RUNNING,
            "dispatcher_trace": response,
        }
