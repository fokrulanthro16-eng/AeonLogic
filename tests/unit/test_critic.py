"""Unit tests: Critic security rule engine."""
from __future__ import annotations

import pytest

from aeonlogic.agents.critic import (
    _RULES,
    _check_hardcoded_credentials,
    _check_hardcoded_secret,
    _check_missing_input_validation,
    _check_missing_jwt_expiry,
    _check_missing_rate_limiting,
)
from aeonlogic.domain.finding import FindingSeverity
from aeonlogic.models.qwen_client import _SECURE_AUTH_CODE, _WEAK_AUTH_CODE


# ── Helper ────────────────────────────────────────────────────────────────────

def _run_all_rules(content: str) -> dict[str, tuple[bool, str]]:
    """Return {rule_id: (matched, evidence)} for every registered rule."""
    return {
        rule_id: checker(content)
        for rule_id, _, _, _, _, checker in _RULES
    }


# ── Weak artifact — all 5 rules must fire ────────────────────────────────────

def test_weak_code_triggers_exactly_five_rules() -> None:
    results = _run_all_rules(_WEAK_AUTH_CODE)
    matched = [rid for rid, (m, _) in results.items() if m]
    assert len(matched) == 5, f"Expected 5 findings, got {matched}"


def test_sec001_hardcoded_secret_fires_on_weak_code() -> None:
    matched, evidence = _check_hardcoded_secret(_WEAK_AUTH_CODE)
    assert matched
    assert "SECRET_KEY" in evidence
    assert '"' in evidence  # literal string value present


def test_sec002_hardcoded_credentials_fires_on_weak_code() -> None:
    matched, evidence = _check_hardcoded_credentials(_WEAK_AUTH_CODE)
    assert matched
    # Evidence is the comparison expression
    assert "==" in evidence


def test_sec003_missing_validation_fires_on_weak_code() -> None:
    matched, evidence = _check_missing_input_validation(_WEAK_AUTH_CODE)
    assert matched
    assert "login" in evidence
    # No type hints in the untyped signature
    assert ": str" not in evidence


def test_sec004_missing_jwt_expiry_fires_on_weak_code() -> None:
    matched, evidence = _check_missing_jwt_expiry(_WEAK_AUTH_CODE)
    assert matched
    assert "jwt.encode" in evidence


def test_sec005_missing_rate_limit_fires_on_weak_code() -> None:
    matched, _ = _check_missing_rate_limiting(_WEAK_AUTH_CODE)
    assert matched


def test_all_weak_findings_have_non_empty_evidence() -> None:
    for rule_id, _, _, _, _, checker in _RULES:
        matched, evidence = checker(_WEAK_AUTH_CODE)
        if matched:
            assert evidence.strip(), f"{rule_id}: matched but evidence is empty"


# ── Secure artifact — zero rules must fire ────────────────────────────────────

def test_secure_code_triggers_no_rules() -> None:
    results = _run_all_rules(_SECURE_AUTH_CODE)
    matched = [rid for rid, (m, _) in results.items() if m]
    assert matched == [], f"Unexpected findings on secure code: {matched}"


def test_sec001_does_not_fire_on_secure_code() -> None:
    matched, _ = _check_hardcoded_secret(_SECURE_AUTH_CODE)
    assert not matched


def test_sec002_does_not_fire_on_secure_code() -> None:
    matched, _ = _check_hardcoded_credentials(_SECURE_AUTH_CODE)
    assert not matched


def test_sec004_does_not_fire_on_secure_code() -> None:
    matched, _ = _check_missing_jwt_expiry(_SECURE_AUTH_CODE)
    assert not matched


def test_sec005_does_not_fire_on_secure_code() -> None:
    matched, _ = _check_missing_rate_limiting(_SECURE_AUTH_CODE)
    assert not matched


# ── Rule registry structure ───────────────────────────────────────────────────

def test_rule_registry_has_five_rules() -> None:
    assert len(_RULES) == 5


def test_sec001_and_sec002_are_critical_severity() -> None:
    critical = {rid for rid, _, sev, _, _, _ in _RULES if sev == FindingSeverity.CRITICAL}
    assert "SEC-001" in critical
    assert "SEC-002" in critical


def test_sec003_and_sec004_are_high_severity() -> None:
    high = {rid for rid, _, sev, _, _, _ in _RULES if sev == FindingSeverity.HIGH}
    assert "SEC-003" in high
    assert "SEC-004" in high


def test_sec005_is_medium_severity() -> None:
    medium = {rid for rid, _, sev, _, _, _ in _RULES if sev == FindingSeverity.MEDIUM}
    assert "SEC-005" in medium
