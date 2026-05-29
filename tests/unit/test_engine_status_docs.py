"""Phase 4F: ENGINE_STATUS.md existence and content checks."""
from __future__ import annotations

from pathlib import Path

import pytest

# Resolve repo root from this file's location: tests/unit/ -> tests/ -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[2]
_ENGINE_STATUS = _REPO_ROOT / "docs" / "ENGINE_STATUS.md"
_README = _REPO_ROOT / "README.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# ENGINE_STATUS.md — existence
# ---------------------------------------------------------------------------

def test_engine_status_file_exists() -> None:
    assert _ENGINE_STATUS.exists(), f"Expected {_ENGINE_STATUS} to exist"


def test_engine_status_is_non_empty() -> None:
    assert len(_read(_ENGINE_STATUS).strip()) > 0


# ---------------------------------------------------------------------------
# ENGINE_STATUS.md — required content
# ---------------------------------------------------------------------------

def test_engine_status_contains_recursive_self_healing() -> None:
    assert "Recursive self-healing" in _read(_ENGINE_STATUS)


def test_engine_status_contains_chromadb() -> None:
    assert "ChromaDB" in _read(_ENGINE_STATUS)


def test_engine_status_contains_neo4j() -> None:
    assert "Neo4j" in _read(_ENGINE_STATUS)


def test_engine_status_contains_hybrid_memory() -> None:
    content = _read(_ENGINE_STATUS)
    assert "Hybrid memory" in content or "hybrid memory" in content


def test_engine_status_contains_qwen_mock_fallback() -> None:
    assert "Qwen mock fallback" in _read(_ENGINE_STATUS)


# ---------------------------------------------------------------------------
# ENGINE_STATUS.md — phase completeness
# ---------------------------------------------------------------------------

def test_engine_status_lists_all_phases() -> None:
    content = _read(_ENGINE_STATUS)
    for phase in ("4A", "4B", "4C", "4D", "4E", "4F"):
        assert phase in content, f"Phase {phase} missing from ENGINE_STATUS.md"


def test_engine_status_contains_run_command() -> None:
    assert "aeonlogic" in _read(_ENGINE_STATUS)


def test_engine_status_contains_test_command() -> None:
    assert "pytest" in _read(_ENGINE_STATUS)


def test_engine_status_mentions_deterministic_repair_loop() -> None:
    content = _read(_ENGINE_STATUS)
    assert "repair loop" in content or "Repair loop" in content


def test_engine_status_mentions_fallback_chain() -> None:
    content = _read(_ENGINE_STATUS)
    assert "fallback" in content.lower()


# ---------------------------------------------------------------------------
# README.md — references ENGINE_STATUS.md
# ---------------------------------------------------------------------------

def test_readme_references_engine_status() -> None:
    assert "ENGINE_STATUS.md" in _read(_README)


def test_readme_mentions_pytest() -> None:
    assert "pytest" in _read(_README)


# ---------------------------------------------------------------------------
# Other docs — key accuracy checks
# ---------------------------------------------------------------------------

def test_state_machine_doc_uses_aeon_state() -> None:
    path = _REPO_ROOT / "docs" / "STATE_MACHINE.md"
    assert "AeonState" in _read(path), "STATE_MACHINE.md should reference AeonState, not AgentState"


def test_system_design_doc_mentions_chroma_store() -> None:
    path = _REPO_ROOT / "docs" / "SYSTEM_DESIGN.md"
    assert "chroma_store" in _read(path)


def test_system_design_doc_mentions_neo4j_store() -> None:
    path = _REPO_ROOT / "docs" / "SYSTEM_DESIGN.md"
    assert "neo4j_store" in _read(path)


def test_whitepaper_mentions_phase_4_implementation() -> None:
    path = _REPO_ROOT / "docs" / "WHITEPAPER_SUMMARY.md"
    assert "Phase 4" in _read(path)
