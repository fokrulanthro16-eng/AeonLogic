"""Unit tests: Dispatcher risk classification and model routing."""
from __future__ import annotations

import pytest

from aeonlogic.agents.dispatcher import _classify_risk
from aeonlogic.domain.task import ModelTier, RiskLevel
from aeonlogic.models.router import route_model


# ── Risk classification ───────────────────────────────────────────────────────

@pytest.mark.parametrize("goal", [
    "Build a secure API authentication module",
    "Implement JWT token-based auth",
    "Design password reset with security best practices",
    "Audit credentials and access control policies",
    "Create an OAuth2 authorization server",
])
def test_security_task_classifies_as_high_risk(goal: str) -> None:
    assert _classify_risk(goal) == RiskLevel.HIGH


@pytest.mark.parametrize("goal", [
    "Generate a summary of recent news articles",
    "List the top 10 Python libraries",
    "Write a hello world program",
    "Explain how quicksort works",
])
def test_generic_task_classifies_as_medium_risk(goal: str) -> None:
    assert _classify_risk(goal) == RiskLevel.MEDIUM


# ── Model routing ─────────────────────────────────────────────────────────────

def test_high_risk_routes_to_strong_model() -> None:
    assert route_model(RiskLevel.HIGH) == ModelTier.STRONG


def test_medium_risk_routes_to_fast_model() -> None:
    assert route_model(RiskLevel.MEDIUM) == ModelTier.FAST


def test_low_risk_routes_to_fast_model() -> None:
    assert route_model(RiskLevel.LOW) == ModelTier.FAST


# ── Auth demo goal specifically ───────────────────────────────────────────────

def test_demo_goal_routes_to_qwen_plus() -> None:
    from aeonlogic.models.budgets import get_budget

    goal = "Build a secure API authentication module"
    tier = route_model(_classify_risk(goal))
    budget = get_budget(tier)
    assert budget.model_name == "qwen-plus"
