"""Unit tests for Phase 6F: Alibaba/Qwen Cloud Proof Pack.

Verifies that ARCHITECTURE.md, ALIBABA_CLOUD_PROOF.md, the updated
DEVPOST_SUBMISSION.md, and README.md all contain the required proof
keywords and structural sections.

All tests are pure file reads — no network, no external services,
no Streamlit runtime, no API key required.
"""
from __future__ import annotations

import pathlib

import pytest

_ROOT = pathlib.Path(__file__).parent.parent.parent
DOCS_ROOT = _ROOT / "docs"
README_PATH = _ROOT / "README.md"
ARCH_PATH = DOCS_ROOT / "ARCHITECTURE.md"
PROOF_PATH = DOCS_ROOT / "ALIBABA_CLOUD_PROOF.md"
DEVPOST_PATH = DOCS_ROOT / "DEVPOST_SUBMISSION.md"


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# docs/ARCHITECTURE.md
# ---------------------------------------------------------------------------

class TestArchitectureDoc:
    @pytest.fixture(scope="class")
    def text(self):
        return _read(ARCH_PATH)

    def test_file_exists(self):
        assert ARCH_PATH.exists(), f"Missing: {ARCH_PATH}"

    def test_contains_alibaba_cloud(self, text):
        assert "Alibaba Cloud" in text

    def test_contains_qwen_cloud(self, text):
        assert "Qwen Cloud" in text

    def test_contains_architecture_diagram(self, text):
        assert "```mermaid" in text or "mermaid" in text.lower()

    def test_contains_qwen_client_path(self, text):
        assert "qwen_client.py" in text

    def test_contains_streamlit_demo_path(self, text):
        assert "streamlit_demo.py" in text

    def test_contains_qwen_api_key(self, text):
        assert "QWEN_API_KEY" in text

    def test_contains_mock_and_fallback(self, text):
        assert "mock" in text.lower()
        assert "fallback" in text.lower()

    def test_contains_no_key_committed(self, text):
        lower = text.lower()
        assert "committed" in lower or "never commit" in lower or "not committed" in lower

    def test_has_streamlit_command_center(self, text):
        assert "Streamlit Command Center" in text

    def test_has_chromadb(self, text):
        assert "ChromaDB" in text

    def test_has_neo4j(self, text):
        assert "Neo4j" in text

    def test_has_dashscope_endpoint(self, text):
        assert "dashscope" in text.lower()

    def test_has_environment_variables_section(self, text):
        assert "environment" in text.lower() or "Environment" in text


# ---------------------------------------------------------------------------
# docs/ALIBABA_CLOUD_PROOF.md
# ---------------------------------------------------------------------------

class TestAlibabaCloudProof:
    @pytest.fixture(scope="class")
    def text(self):
        return _read(PROOF_PATH)

    def test_file_exists(self):
        assert PROOF_PATH.exists(), f"Missing: {PROOF_PATH}"

    def test_contains_alibaba_cloud(self, text):
        assert "Alibaba Cloud" in text

    def test_contains_qwen_cloud(self, text):
        assert "Qwen Cloud" in text

    def test_contains_qwen_client_path(self, text):
        assert "qwen_client.py" in text

    def test_contains_streamlit_demo_path(self, text):
        assert "streamlit_demo.py" in text

    def test_contains_qwen_api_key(self, text):
        assert "QWEN_API_KEY" in text

    def test_contains_safe_mock_fallback(self, text):
        lower = text.lower()
        assert "mock" in lower
        assert "fallback" in lower

    def test_no_api_key_committed(self, text):
        lower = text.lower()
        assert "committed" in lower or "never commit" in lower or "not committed" in lower

    def test_has_deployment_checklist(self, text):
        lower = text.lower()
        assert "checklist" in lower or "proof" in lower

    def test_has_env_example_reference(self, text):
        assert ".env.example" in text

    def test_has_architecture_reference(self, text):
        assert "ARCHITECTURE" in text or "architecture diagram" in text.lower()

    def test_has_live_demo_placeholder(self, text):
        lower = text.lower()
        assert "live demo" in lower or "demo url" in lower

    def test_has_demo_video_placeholder(self, text):
        lower = text.lower()
        assert "demo video" in lower or "video" in lower

    def test_has_github_repo_placeholder(self, text):
        lower = text.lower()
        assert "github" in lower or "repo" in lower

    def test_has_mask_api_key_reference(self, text):
        assert "mask_api_key" in text or "masked" in text.lower()


# ---------------------------------------------------------------------------
# docs/DEVPOST_SUBMISSION.md (updated)
# ---------------------------------------------------------------------------

class TestDevpostSubmissionUpdated:
    @pytest.fixture(scope="class")
    def text(self):
        return _read(DEVPOST_PATH)

    def test_contains_alibaba_cloud(self, text):
        assert "Alibaba Cloud" in text

    def test_has_architecture_diagram_reference(self, text):
        assert "ARCHITECTURE" in text or "architecture diagram" in text.lower() or "mermaid" in text.lower()

    def test_has_demo_video_placeholder(self, text):
        lower = text.lower()
        assert "demo video" in lower or "video" in lower

    def test_has_live_demo_placeholder(self, text):
        lower = text.lower()
        assert "live demo" in lower or "demo url" in lower or "localhost" in lower

    def test_contains_qwen_api_key(self, text):
        assert "QWEN_API_KEY" in text

    def test_contains_qwen_client_path(self, text):
        assert "qwen_client.py" in text

    def test_has_alibaba_cloud_proof_link(self, text):
        assert "ALIBABA_CLOUD_PROOF" in text or "Alibaba Cloud" in text

    def test_still_has_self_healing(self, text):
        assert "self-healing" in text

    def test_still_has_chromadb(self, text):
        assert "ChromaDB" in text


# ---------------------------------------------------------------------------
# README.md (updated)
# ---------------------------------------------------------------------------

class TestReadmeUpdated:
    @pytest.fixture(scope="class")
    def text(self):
        return _read(README_PATH)

    def test_contains_alibaba_cloud(self, text):
        assert "Alibaba Cloud" in text

    def test_has_architecture_doc_link(self, text):
        assert "ARCHITECTURE" in text

    def test_has_alibaba_cloud_proof_link(self, text):
        assert "ALIBABA_CLOUD_PROOF" in text

    def test_contains_qwen_api_key(self, text):
        assert "QWEN_API_KEY" in text

    def test_has_mock_mode_note(self, text):
        assert "mock" in text.lower()

    def test_has_no_key_committed_statement(self, text):
        lower = text.lower()
        assert "committed" in lower or "never commit" in lower or "not committed" in lower

    def test_still_has_self_healing(self, text):
        assert "self-healing" in text

    def test_still_has_chromadb(self, text):
        assert "ChromaDB" in text

    def test_still_has_streamlit_command_center(self, text):
        assert "Streamlit Command Center" in text
