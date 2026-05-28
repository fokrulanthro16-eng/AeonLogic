from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from aeonlogic.agents.base import BaseAgent
from aeonlogic.domain.finding import Finding, FindingSeverity, Verdict
from aeonlogic.domain.task import ModelTier
from aeonlogic.graph.state import AeonState
from aeonlogic.models.budgets import get_budget
from aeonlogic.models.prompts import critique_prompt
from aeonlogic.models.qwen_client import get_client

# ── Security rule checkers ────────────────────────────────────────────────────
# Each returns (matched: bool, evidence: str)

def _check_hardcoded_secret(content: str) -> tuple[bool, str]:
    m = re.search(
        r"(SECRET_KEY|API_KEY|SECRET|PRIVATE_KEY|PASSWD)\s*=\s*['\"][^'\"]{3,}['\"]",
        content,
        re.IGNORECASE,
    )
    return (True, m.group(0).strip()[:120]) if m else (False, "")


def _check_hardcoded_credentials(content: str) -> tuple[bool, str]:
    m = re.search(
        r"(username|password|passwd)\s*==\s*['\"][^'\"]+['\"]",
        content,
        re.IGNORECASE,
    )
    return (True, m.group(0).strip()[:120]) if m else (False, "")


def _check_missing_input_validation(content: str) -> tuple[bool, str]:
    # Auth function with no type hints: parameters have no `: type` annotation
    m = re.search(
        r"def\s+(login|authenticate|auth)\s*\(\s*\w+\s*,\s*\w+\s*\)\s*:",
        content,
    )
    return (True, m.group(0).strip()[:120]) if m else (False, "")


def _check_missing_jwt_expiry(content: str) -> tuple[bool, str]:
    if "jwt.encode" in content and '"exp"' not in content and "'exp'" not in content:
        m = re.search(r"jwt\.encode\([^)]{0,120}\)", content, re.DOTALL)
        evidence = m.group(0).replace("\n", " ").strip()[:120] if m else "jwt.encode(...) missing exp claim"
        return True, evidence
    return False, ""


def _check_missing_rate_limiting(content: str) -> tuple[bool, str]:
    has_auth_fn = bool(
        re.search(r"def\s+(login|authenticate|auth)\s*\(", content, re.IGNORECASE)
    )
    if not has_auth_fn:
        return False, ""
    keywords = ("rate_limit", "ratelimit", "rate_tracker", "throttle", "max_attempt", "lockout", "rate limit")
    if not any(kw in content.lower() for kw in keywords):
        return True, "No rate limiting mechanism found in authentication function"
    return False, ""


# ── Rule registry ─────────────────────────────────────────────────────────────
# (rule_id, title, severity, category, recommendation, checker)
_RULES: list[tuple[str, str, FindingSeverity, str, str, Callable[[str], tuple[bool, str]]]] = [
    (
        "SEC-001",
        "Hardcoded Secret",
        FindingSeverity.CRITICAL,
        "secret-management",
        "Load all secrets from environment variables: os.environ['SECRET_KEY']. "
        "Never embed secrets in source code.",
        _check_hardcoded_secret,
    ),
    (
        "SEC-002",
        "Hardcoded Credentials",
        FindingSeverity.CRITICAL,
        "authentication",
        "Replace hardcoded credential comparisons with a secure store and "
        "password hashing (bcrypt/argon2).",
        _check_hardcoded_credentials,
    ),
    (
        "SEC-003",
        "Missing Input Validation",
        FindingSeverity.HIGH,
        "input-validation",
        "Add type hints and explicit validation: check types, lengths, and "
        "format before processing any input.",
        _check_missing_input_validation,
    ),
    (
        "SEC-004",
        "JWT Token Missing Expiry",
        FindingSeverity.HIGH,
        "token-security",
        "Always include an 'exp' claim in JWT payloads. "
        "Use short-lived tokens: datetime.utcnow() + timedelta(hours=1).",
        _check_missing_jwt_expiry,
    ),
    (
        "SEC-005",
        "Missing Rate Limiting",
        FindingSeverity.MEDIUM,
        "availability",
        "Implement rate limiting on authentication endpoints to prevent "
        "brute-force attacks.",
        _check_missing_rate_limiting,
    ),
]


class CriticAgent(BaseAgent):
    name = "critic"

    def __call__(self, state: AeonState) -> dict[str, Any]:
        active_task = state["active_task"]
        if active_task is None:
            raise ValueError("CriticAgent: no active_task in state")
        artifact = state["candidate_artifact"]
        if artifact is None:
            raise ValueError("CriticAgent: no candidate_artifact in state")

        attempt = state.get("generation_attempt") or 1  # type: ignore[call-overload]

        # Consume a mock LLM call (models layer; no-op in Phase 2 mock)
        client = get_client()
        budget = get_budget(ModelTier.STRONG)
        client.complete(
            budget=budget,
            prompt=critique_prompt(active_task.description, artifact.content),
        )

        # Run all security rules against the artifact content
        findings: list[Finding] = []
        for rule_id, title, severity, category, recommendation, checker in _RULES:
            matched, evidence = checker(artifact.content)
            if matched:
                findings.append(
                    Finding(
                        artifact_id=artifact.id,
                        severity=severity,
                        category=category,
                        title=f"[{rule_id}] {title}",
                        description=f"{title} detected in attempt {attempt}.",
                        evidence=evidence,
                        recommendation=recommendation,
                    )
                )

        if findings:
            return {
                "critic_verdict": Verdict.REJECTED,
                "critic_findings": findings,
                "critic_trace": (
                    f"REJECTED (attempt {attempt}) -> {len(findings)} security finding(s)"
                ),
            }

        return {
            "critic_verdict": Verdict.APPROVED,
            "critic_findings": [],
            "critic_trace": (
                f"APPROVED (attempt {attempt}) -> all {len(_RULES)} security checks passed"
            ),
        }
