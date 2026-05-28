"""Integration tests: CLI output for the auth demo task."""
from __future__ import annotations

import pytest
from typer.testing import CliRunner

from aeonlogic.app.cli import app

_GOAL = "Build a secure API authentication module"


@pytest.fixture(scope="module")
def cli_result():
    """Invoke the CLI once per module and return the captured result."""
    runner = CliRunner()
    return runner.invoke(app, [_GOAL])


# ── Exit code ─────────────────────────────────────────────────────────────────

def test_exit_code_is_zero(cli_result) -> None:
    if cli_result.exception:
        raise cli_result.exception
    assert cli_result.exit_code == 0


# ── FINAL panel assertions ────────────────────────────────────────────────────

def test_output_contains_success_status(cli_result) -> None:
    assert "Status    : SUCCESS" in cli_result.output


def test_output_contains_attempts_2(cli_result) -> None:
    assert "Attempts  : 2" in cli_result.output


def test_output_contains_repaired_yes(cli_result) -> None:
    assert "Repaired  : YES" in cli_result.output


def test_output_contains_approved_verdict(cli_result) -> None:
    assert "Verdict   : APPROVED" in cli_result.output


def test_output_contains_5_findings_resolved(cli_result) -> None:
    assert "5 detected, 5 resolved" in cli_result.output


# ── Stage label assertions ────────────────────────────────────────────────────

def test_output_shows_dispatch_stage(cli_result) -> None:
    assert "[DISPATCH]" in cli_result.output


def test_output_shows_generate_stage(cli_result) -> None:
    assert "[GENERATE]" in cli_result.output


def test_output_shows_critic_rejection(cli_result) -> None:
    assert "REJECTED" in cli_result.output


def test_output_shows_execute_blocked(cli_result) -> None:
    assert "BLOCKED" in cli_result.output


def test_output_shows_repair_stage(cli_result) -> None:
    assert "[REPAIR]" in cli_result.output


def test_output_shows_critic_approved(cli_result) -> None:
    assert "APPROVED" in cli_result.output


def test_output_shows_execute_success(cli_result) -> None:
    assert "SUCCESS" in cli_result.output


def test_output_shows_memory_stage(cli_result) -> None:
    assert "[MEMORY]" in cli_result.output


def test_output_shows_final_panel(cli_result) -> None:
    assert "FINAL" in cli_result.output


# ── Model routing visible in output ──────────────────────────────────────────

def test_output_shows_qwen_plus_for_high_risk_task(cli_result) -> None:
    assert "qwen-plus" in cli_result.output


def test_output_shows_strong_tier(cli_result) -> None:
    assert "STRONG" in cli_result.output


# ── Security findings visible in output ──────────────────────────────────────

def test_output_shows_sec001_finding(cli_result) -> None:
    assert "SEC-001" in cli_result.output


def test_output_shows_sec002_finding(cli_result) -> None:
    assert "SEC-002" in cli_result.output
