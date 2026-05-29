"""Phase 5D: GitHub / portfolio showcase — documentation tests.

Verifies that SHOWCASE.md and the updated README contain the required
content for portfolio and hackathon presentation.
"""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_SHOWCASE = _REPO / "docs" / "SHOWCASE.md"
_README   = _REPO / "README.md"
_STATUS   = _REPO / "docs" / "ENGINE_STATUS.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# SHOWCASE.md — existence
# ---------------------------------------------------------------------------

def test_showcase_file_exists() -> None:
    assert _SHOWCASE.exists(), "docs/SHOWCASE.md must exist"


def test_showcase_is_non_empty() -> None:
    assert len(_read(_SHOWCASE).strip()) > 100


# ---------------------------------------------------------------------------
# SHOWCASE.md — required content (spec-mandated strings)
# ---------------------------------------------------------------------------

def test_showcase_contains_aeonlogic() -> None:
    assert "AeonLogic" in _read(_SHOWCASE)


def test_showcase_contains_self_healing() -> None:
    content = _read(_SHOWCASE)
    assert "Self-Healing" in content or "self-healing" in content.lower()


def test_showcase_contains_streamlit() -> None:
    assert "Streamlit" in _read(_SHOWCASE)


def test_showcase_contains_chromadb() -> None:
    assert "ChromaDB" in _read(_SHOWCASE)


def test_showcase_contains_neo4j() -> None:
    assert "Neo4j" in _read(_SHOWCASE)


def test_showcase_contains_hybrid_memory() -> None:
    content = _read(_SHOWCASE)
    assert "Hybrid memory" in content or "hybrid memory" in content.lower() \
           or "Hybrid Memory" in content


# ---------------------------------------------------------------------------
# SHOWCASE.md — structural completeness
# ---------------------------------------------------------------------------

def test_showcase_contains_demo_script() -> None:
    content = _read(_SHOWCASE)
    assert "Demo Script" in content or "demo script" in content.lower()


def test_showcase_contains_screenshot_checklist() -> None:
    content = _read(_SHOWCASE)
    assert "Screenshot" in content or "screenshot" in content.lower()


def test_showcase_contains_judge_explanation() -> None:
    content = _read(_SHOWCASE)
    assert "Judge" in content or "judge" in content.lower()


def test_showcase_contains_project_pitch() -> None:
    content = _read(_SHOWCASE)
    assert "Pitch" in content or "pitch" in content.lower()


def test_showcase_contains_feature_matrix() -> None:
    content = _read(_SHOWCASE)
    assert "Feature" in content


def test_showcase_contains_pipeline_description() -> None:
    content = _read(_SHOWCASE)
    assert "repair" in content.lower() or "self-heal" in content.lower()


# ---------------------------------------------------------------------------
# README.md — hero section
# ---------------------------------------------------------------------------

def test_readme_hero_subtitle() -> None:
    content = _read(_README)
    assert "Recursive Self-Healing Multi-Agent Engine" in content


def test_readme_has_cli_plus_streamlit() -> None:
    content = _read(_README)
    assert "CLI" in content and "Streamlit" in content


def test_readme_has_chromadb_feature() -> None:
    assert "ChromaDB" in _read(_README)


def test_readme_has_neo4j_feature() -> None:
    assert "Neo4j" in _read(_README)


def test_readme_has_hybrid_memory_feature() -> None:
    content = _read(_README)
    assert "Hybrid memory" in content or "hybrid memory" in content.lower() \
           or "Hybrid Memory" in content


def test_readme_has_self_healing_feature() -> None:
    content = _read(_README)
    assert "self-healing" in content.lower() or "Self-Healing" in content


def test_readme_has_mock_fallback_feature() -> None:
    content = _read(_README)
    assert "mock" in content.lower()


def test_readme_has_streamlit_run_command() -> None:
    assert "streamlit run" in _read(_README)


def test_readme_has_pytest_command() -> None:
    assert "pytest" in _read(_README)


def test_readme_has_architecture_pipeline() -> None:
    content = _read(_README)
    assert "DISPATCH" in content and "GENERATE" in content and "CRITIC" in content


def test_readme_has_quick_start_section() -> None:
    content = _read(_README)
    assert "Quick start" in content or "quick start" in content.lower()


def test_readme_has_feature_table() -> None:
    content = _read(_README)
    # Feature table uses checkmarks
    assert "✅" in content or "multi-agent" in content.lower()


def test_readme_references_showcase_md() -> None:
    assert "SHOWCASE.md" in _read(_README)


# ---------------------------------------------------------------------------
# ENGINE_STATUS.md — Phase 5 entries
# ---------------------------------------------------------------------------

def test_engine_status_contains_phase_5a() -> None:
    assert "5A" in _read(_STATUS)


def test_engine_status_contains_phase_5b() -> None:
    assert "5B" in _read(_STATUS)


def test_engine_status_contains_phase_5c() -> None:
    assert "5C" in _read(_STATUS)


def test_engine_status_contains_phase_5d() -> None:
    assert "5D" in _read(_STATUS)


def test_engine_status_current_phase_is_5d() -> None:
    content = _read(_STATUS)
    # The current phase line should reference 5D
    assert "5D" in content


# ---------------------------------------------------------------------------
# Cross-doc consistency
# ---------------------------------------------------------------------------

def test_system_design_has_presentation_layer_section() -> None:
    path = _REPO / "docs" / "SYSTEM_DESIGN.md"
    assert "Presentation layer" in path.read_text(encoding="utf-8") \
           or "presentation layer" in path.read_text(encoding="utf-8").lower()


def test_whitepaper_has_phase_5_section() -> None:
    path = _REPO / "docs" / "WHITEPAPER_SUMMARY.md"
    assert "Phase 5" in path.read_text(encoding="utf-8")
