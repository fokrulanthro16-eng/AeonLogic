"""Unit tests for Phase 6C: Artifact Preview UI helpers.

Covers:
  - artifact_status_label  — status label text
  - extract_artifact_preview — data extraction from final pipeline state
  - build_artifact_preview_html — HTML with and without artifact content
"""
from __future__ import annotations

import pytest

from aeonlogic.app.streamlit_demo import (
    ARTIFACT_PREVIEW_MAX_CHARS,
    ARTIFACT_PREVIEW_UNAVAILABLE,
    artifact_status_label,
    build_artifact_preview_html,
    extract_artifact_preview,
)


# ---------------------------------------------------------------------------
# artifact_status_label
# ---------------------------------------------------------------------------

class TestArtifactStatusLabel:
    def test_success_returns_approved(self):
        assert artifact_status_label("SUCCESS") == "APPROVED"

    def test_success_substring_in_longer_string(self):
        assert artifact_status_label("CYCLESTATUS.SUCCESS") == "APPROVED"

    def test_fail_returns_rejected(self):
        assert artifact_status_label("FAILED") == "REJECTED"

    def test_error_returns_rejected(self):
        assert artifact_status_label("ERROR") == "REJECTED"

    def test_unknown_status_returns_unknown(self):
        assert artifact_status_label("RUNNING") == "UNKNOWN"

    def test_empty_string_returns_unknown(self):
        assert artifact_status_label("") == "UNKNOWN"

    def test_case_insensitive_success(self):
        assert artifact_status_label("success") == "APPROVED"

    def test_case_insensitive_fail(self):
        assert artifact_status_label("failed") == "REJECTED"


# ---------------------------------------------------------------------------
# extract_artifact_preview
# ---------------------------------------------------------------------------

class TestExtractArtifactPreview:
    def test_empty_state_returns_none_fields(self):
        result = extract_artifact_preview({})
        assert result["artifact_text"] is None
        assert result["session_id"] is None

    def test_extracts_content_from_artifact_object(self):
        class FakeArtifact:
            content = "def hello(): pass"

        result = extract_artifact_preview({"candidate_artifact": FakeArtifact()})
        assert result["artifact_text"] == "def hello(): pass"

    def test_handles_string_artifact(self):
        result = extract_artifact_preview({"candidate_artifact": "raw code string"})
        assert result["artifact_text"] == "raw code string"

    def test_none_artifact_gives_none_text(self):
        result = extract_artifact_preview(
            {"candidate_artifact": None, "session_id": "sess99"}
        )
        assert result["artifact_text"] is None
        assert result["session_id"] == "sess99"

    def test_extracts_session_id(self):
        result = extract_artifact_preview({"session_id": "abc123"})
        assert result["session_id"] == "abc123"

    def test_empty_content_attribute_gives_none_text(self):
        class FakeArtifact:
            content = ""

        result = extract_artifact_preview({"candidate_artifact": FakeArtifact()})
        assert result["artifact_text"] is None

    def test_empty_string_artifact_gives_none_text(self):
        result = extract_artifact_preview({"candidate_artifact": ""})
        assert result["artifact_text"] is None

    def test_no_session_id_key_gives_none(self):
        result = extract_artifact_preview({"candidate_artifact": "code"})
        assert result["session_id"] is None


# ---------------------------------------------------------------------------
# build_artifact_preview_html — with artifact content
# ---------------------------------------------------------------------------

class TestBuildArtifactPreviewHtmlWithContent:
    def test_contains_artifact_text(self):
        html = build_artifact_preview_html("def foo(): pass", "sess001")
        assert "def foo(): pass" in html

    def test_contains_session_id(self):
        html = build_artifact_preview_html("code here", "mysession123456")
        assert "mysession123456" in html

    def test_does_not_show_unavailable_message(self):
        html = build_artifact_preview_html("some code", "s1")
        assert ARTIFACT_PREVIEW_UNAVAILABLE not in html

    def test_long_content_is_truncated_with_ellipsis(self):
        long_code = "x" * (ARTIFACT_PREVIEW_MAX_CHARS + 100)
        html = build_artifact_preview_html(long_code, None)
        assert "…" in html

    def test_long_content_does_not_exceed_limit(self):
        long_code = "a" * (ARTIFACT_PREVIEW_MAX_CHARS + 100)
        html = build_artifact_preview_html(long_code, None)
        assert "a" * (ARTIFACT_PREVIEW_MAX_CHARS + 1) not in html

    def test_exact_length_content_has_no_ellipsis(self):
        exact_code = "z" * ARTIFACT_PREVIEW_MAX_CHARS
        html = build_artifact_preview_html(exact_code, None)
        assert "…" not in html
        assert exact_code in html

    def test_returns_html_string(self):
        html = build_artifact_preview_html("code", "sid")
        assert isinstance(html, str)
        assert "<" in html


# ---------------------------------------------------------------------------
# build_artifact_preview_html — without artifact content
# ---------------------------------------------------------------------------

class TestBuildArtifactPreviewHtmlNoContent:
    def test_shows_unavailable_message_when_none(self):
        html = build_artifact_preview_html(None, None)
        assert ARTIFACT_PREVIEW_UNAVAILABLE in html

    def test_shows_unavailable_message_when_empty_string(self):
        html = build_artifact_preview_html("", "s2")
        assert ARTIFACT_PREVIEW_UNAVAILABLE in html

    def test_no_session_footer_when_session_id_is_none(self):
        html = build_artifact_preview_html(None, None)
        assert "SESSION" not in html

    def test_session_footer_present_when_session_id_given(self):
        html = build_artifact_preview_html(None, "mysess")
        assert "SESSION" in html
        assert "mysess" in html

    def test_returns_html_string(self):
        html = build_artifact_preview_html(None, None)
        assert isinstance(html, str)
        assert "<" in html
