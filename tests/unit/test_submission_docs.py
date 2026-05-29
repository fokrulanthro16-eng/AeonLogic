"""Unit tests for Phase 6E: Devpost Submission Pack.

Verifies that all three submission documents contain the required keywords
and structural sections. All tests are pure file reads — no external
services, network, or Streamlit runtime required.
"""
from __future__ import annotations

import pathlib

import pytest

_ROOT = pathlib.Path(__file__).parent.parent.parent
DOCS_ROOT = _ROOT / "docs"
README_PATH = _ROOT / "README.md"
DEVPOST_PATH = DOCS_ROOT / "DEVPOST_SUBMISSION.md"
DEMO_SCRIPT_PATH = DOCS_ROOT / "DEMO_SCRIPT.md"


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# docs/DEVPOST_SUBMISSION.md
# ---------------------------------------------------------------------------

class TestDevpostSubmission:
    @pytest.fixture(scope="class")
    def text(self):
        return _read(DEVPOST_PATH)

    def test_file_exists(self):
        assert DEVPOST_PATH.exists(), f"Missing: {DEVPOST_PATH}"

    def test_contains_aeonlogic(self, text):
        assert "AeonLogic" in text

    def test_contains_qwen_cloud(self, text):
        assert "Qwen Cloud" in text

    def test_contains_self_healing(self, text):
        assert "self-healing" in text

    def test_contains_streamlit_command_center(self, text):
        assert "Streamlit Command Center" in text

    def test_contains_chromadb(self, text):
        assert "ChromaDB" in text

    def test_contains_hybrid_memory(self, text):
        assert "hybrid memory" in text.lower()

    def test_contains_artifact_preview(self, text):
        assert "artifact preview" in text.lower()

    def test_contains_memory_evidence(self, text):
        assert "memory evidence" in text.lower()

    def test_has_problem_section(self, text):
        assert "problem" in text.lower()

    def test_has_solution_section(self, text):
        assert "solution" in text.lower()

    def test_has_architecture_section(self, text):
        assert "architecture" in text.lower()

    def test_has_what_is_next_section(self, text):
        assert "next" in text.lower()

    def test_has_tagline(self, text):
        assert "tagline" in text.lower() or "Tagline" in text

    def test_has_challenges_section(self, text):
        assert "challenge" in text.lower()

    def test_has_accomplishments_section(self, text):
        assert "accomplishment" in text.lower() or "proud" in text.lower()


# ---------------------------------------------------------------------------
# docs/DEMO_SCRIPT.md
# ---------------------------------------------------------------------------

class TestDemoScript:
    @pytest.fixture(scope="class")
    def text(self):
        return _read(DEMO_SCRIPT_PATH)

    def test_file_exists(self):
        assert DEMO_SCRIPT_PATH.exists(), f"Missing: {DEMO_SCRIPT_PATH}"

    def test_contains_aeonlogic(self, text):
        assert "AeonLogic" in text

    def test_contains_qwen_cloud(self, text):
        assert "Qwen Cloud" in text

    def test_contains_self_healing(self, text):
        assert "self-healing" in text

    def test_contains_streamlit_command_center(self, text):
        assert "Streamlit Command Center" in text

    def test_contains_chromadb(self, text):
        assert "ChromaDB" in text

    def test_contains_hybrid_memory(self, text):
        assert "hybrid memory" in text.lower()

    def test_contains_artifact_preview(self, text):
        assert "artifact preview" in text.lower()

    def test_contains_memory_evidence(self, text):
        assert "memory evidence" in text.lower()

    def test_has_thirty_second_pitch(self, text):
        assert "30" in text or "30-second" in text or "thirty" in text.lower()

    def test_has_demo_script_section(self, text):
        assert "demo" in text.lower()

    def test_has_judge_section(self, text):
        assert "judge" in text.lower()

    def test_has_screenshot_checklist(self, text):
        assert "screenshot" in text.lower()

    def test_has_qa_section(self, text):
        assert "Q&A" in text or "q&a" in text.lower() or "question" in text.lower()

    def test_has_two_minute_script(self, text):
        assert "2-minute" in text.lower() or "2 minute" in text.lower() or "two-minute" in text.lower()

    def test_has_five_minute_section(self, text):
        assert "5-minute" in text.lower() or "5 minute" in text.lower() or "five-minute" in text.lower()


# ---------------------------------------------------------------------------
# README.md
# ---------------------------------------------------------------------------

class TestReadme:
    @pytest.fixture(scope="class")
    def text(self):
        return _read(README_PATH)

    def test_file_exists(self):
        assert README_PATH.exists(), f"Missing: {README_PATH}"

    def test_contains_aeonlogic(self, text):
        assert "AeonLogic" in text

    def test_contains_qwen_cloud(self, text):
        assert "Qwen Cloud" in text

    def test_contains_self_healing(self, text):
        assert "self-healing" in text

    def test_contains_streamlit_command_center(self, text):
        assert "Streamlit Command Center" in text

    def test_contains_chromadb(self, text):
        assert "ChromaDB" in text

    def test_contains_hybrid_memory(self, text):
        assert "hybrid memory" in text.lower()

    def test_contains_artifact_preview(self, text):
        assert "artifact preview" in text.lower()

    def test_contains_memory_evidence(self, text):
        assert "memory evidence" in text.lower()

    def test_has_quick_start(self, text):
        assert "quick start" in text.lower() or "Quick start" in text

    def test_has_architecture_section(self, text):
        assert "architecture" in text.lower() or "Architecture" in text

    def test_has_features_section(self, text):
        assert "feature" in text.lower() or "Feature" in text

    def test_has_devpost_or_submission_doc_link(self, text):
        assert "DEVPOST" in text or "devpost" in text.lower() or "Devpost" in text
