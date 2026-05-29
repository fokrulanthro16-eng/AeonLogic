"""Unit tests for Phase 6D: Memory Evidence UI helpers.

Covers:
  - chroma_status_label   — ChromaDB active / fallback / unavailable
  - neo4j_status_label    — Neo4j configured / not configured / unavailable
  - hybrid_status_label   — Hybrid active / fallback
  - build_memory_evidence — data aggregation; defensive against bad input
  - build_memory_evidence_html — HTML with data / without data
"""
from __future__ import annotations

import pytest

from aeonlogic.app.streamlit_demo import (
    MEMORY_EVIDENCE_UNAVAILABLE,
    build_memory_evidence,
    build_memory_evidence_html,
    chroma_status_label,
    hybrid_status_label,
    neo4j_status_label,
)


# ---------------------------------------------------------------------------
# chroma_status_label
# ---------------------------------------------------------------------------

class TestChromaStatusLabel:
    def test_chroma_memory_store_returns_active(self):
        assert chroma_status_label("ChromaMemoryStore") == "ACTIVE"

    def test_mock_memory_store_returns_fallback(self):
        assert chroma_status_label("MockMemoryStore") == "FALLBACK"

    def test_empty_name_returns_unavailable(self):
        assert chroma_status_label("") == "UNAVAILABLE"

    def test_unknown_name_returns_unavailable(self):
        assert chroma_status_label("SomeOtherStore") == "UNAVAILABLE"


# ---------------------------------------------------------------------------
# neo4j_status_label
# ---------------------------------------------------------------------------

class TestNeo4jStatusLabel:
    def test_configured_and_available_returns_configured(self):
        assert neo4j_status_label(uri_configured=True, neo4j_available=True) == "CONFIGURED"

    def test_not_configured_returns_not_configured(self):
        assert neo4j_status_label(uri_configured=False, neo4j_available=False) == "NOT CONFIGURED"

    def test_configured_but_not_available_returns_unavailable(self):
        assert neo4j_status_label(uri_configured=True, neo4j_available=False) == "UNAVAILABLE"

    def test_uri_not_configured_overrides_availability(self):
        # uri_configured=False always → NOT CONFIGURED regardless of neo4j_available
        assert neo4j_status_label(uri_configured=False, neo4j_available=True) == "NOT CONFIGURED"


# ---------------------------------------------------------------------------
# hybrid_status_label
# ---------------------------------------------------------------------------

class TestHybridStatusLabel:
    def test_active_chroma_returns_active(self):
        assert hybrid_status_label("ACTIVE") == "ACTIVE"

    def test_fallback_chroma_returns_fallback(self):
        assert hybrid_status_label("FALLBACK") == "FALLBACK"

    def test_unavailable_chroma_returns_fallback(self):
        assert hybrid_status_label("UNAVAILABLE") == "FALLBACK"

    def test_unknown_string_returns_fallback(self):
        assert hybrid_status_label("") == "FALLBACK"


# ---------------------------------------------------------------------------
# build_memory_evidence — data aggregation
# ---------------------------------------------------------------------------

class TestBuildMemoryEvidence:
    def _summary(self, lessons=None):
        return {"memory_lessons": lessons or [], "final_status": "SUCCESS"}

    def test_returns_available_true_on_empty_input(self):
        ev = build_memory_evidence(self._summary(), {})
        assert ev["available"] is True

    def test_counts_written_lessons(self):
        lessons = [
            {"type": "failure", "content": "f", "id": "1"},
            {"type": "success", "content": "s1", "id": "2"},
            {"type": "success", "content": "s2", "id": "3"},
        ]
        ev = build_memory_evidence(self._summary(lessons), {})
        assert ev["lessons_written"] == 3
        assert ev["failure_lessons"] == 1
        assert ev["success_lessons"] == 2

    def test_zero_counts_on_no_lessons(self):
        ev = build_memory_evidence(self._summary([]), {})
        assert ev["lessons_written"] == 0
        assert ev["failure_lessons"] == 0
        assert ev["success_lessons"] == 0

    def test_retrieved_count_from_memory_context(self):
        final_state = {"memory_context": {"retrieved_lessons": ["a", "b", "c"]}}
        ev = build_memory_evidence(self._summary(), final_state)
        assert ev["retrieved_count"] == 3

    def test_retrieved_count_zero_when_no_memory_context(self):
        ev = build_memory_evidence(self._summary(), {})
        assert ev["retrieved_count"] == 0

    def test_retrieved_count_zero_when_key_absent(self):
        ev = build_memory_evidence(self._summary(), {"memory_context": {}})
        assert ev["retrieved_count"] == 0

    def test_passthrough_chroma_status(self):
        ev = build_memory_evidence(self._summary(), {}, chroma_status="ACTIVE")
        assert ev["chroma_status"] == "ACTIVE"

    def test_passthrough_neo4j_not_configured(self):
        ev = build_memory_evidence(self._summary(), {}, neo4j_status="NOT CONFIGURED")
        assert ev["neo4j_status"] == "NOT CONFIGURED"

    def test_passthrough_hybrid_fallback(self):
        ev = build_memory_evidence(self._summary(), {}, hybrid_status="FALLBACK")
        assert ev["hybrid_status"] == "FALLBACK"

    def test_never_raises_on_none_summary(self):
        result = build_memory_evidence(None, {})  # type: ignore[arg-type]
        assert isinstance(result, dict)
        assert "available" in result

    def test_never_raises_on_none_final_state(self):
        result = build_memory_evidence(self._summary(), None)  # type: ignore[arg-type]
        assert isinstance(result, dict)
        assert "available" in result

    def test_never_raises_on_both_none(self):
        result = build_memory_evidence(None, None)  # type: ignore[arg-type]
        assert isinstance(result, dict)
        assert "available" in result


# ---------------------------------------------------------------------------
# build_memory_evidence_html — with data
# ---------------------------------------------------------------------------

class TestBuildMemoryEvidenceHtmlWithData:
    def _evidence(self, **overrides):
        base = {
            "available":       True,
            "chroma_status":   "ACTIVE",
            "neo4j_status":    "NOT CONFIGURED",
            "hybrid_status":   "ACTIVE",
            "lessons_written": 2,
            "failure_lessons": 1,
            "success_lessons": 1,
            "retrieved_count": 3,
        }
        base.update(overrides)
        return base

    def test_shows_chroma_active(self):
        html = build_memory_evidence_html(self._evidence(chroma_status="ACTIVE"))
        assert "ACTIVE" in html

    def test_shows_neo4j_not_configured(self):
        html = build_memory_evidence_html(self._evidence(neo4j_status="NOT CONFIGURED"))
        assert "NOT CONFIGURED" in html

    def test_shows_hybrid_fallback(self):
        html = build_memory_evidence_html(self._evidence(hybrid_status="FALLBACK"))
        assert "FALLBACK" in html

    def test_shows_lesson_counts(self):
        html = build_memory_evidence_html(self._evidence(lessons_written=7))
        assert "7" in html

    def test_shows_failure_count(self):
        html = build_memory_evidence_html(self._evidence(failure_lessons=3))
        assert "3" in html

    def test_shows_success_count(self):
        html = build_memory_evidence_html(self._evidence(success_lessons=5))
        assert "5" in html

    def test_shows_retrieved_count(self):
        html = build_memory_evidence_html(self._evidence(retrieved_count=4))
        assert "4" in html

    def test_does_not_show_unavailable_message(self):
        html = build_memory_evidence_html(self._evidence())
        assert MEMORY_EVIDENCE_UNAVAILABLE not in html

    def test_returns_html_string(self):
        html = build_memory_evidence_html(self._evidence())
        assert isinstance(html, str)
        assert "<" in html


# ---------------------------------------------------------------------------
# build_memory_evidence_html — unavailable
# ---------------------------------------------------------------------------

class TestBuildMemoryEvidenceHtmlUnavailable:
    def test_shows_unavailable_message_when_available_false(self):
        html = build_memory_evidence_html({"available": False})
        assert MEMORY_EVIDENCE_UNAVAILABLE in html

    def test_does_not_show_chroma_when_unavailable(self):
        html = build_memory_evidence_html({"available": False})
        assert "CHROMA" not in html

    def test_does_not_show_neo4j_when_unavailable(self):
        html = build_memory_evidence_html({"available": False})
        assert "NEO4J" not in html

    def test_does_not_show_hybrid_when_unavailable(self):
        html = build_memory_evidence_html({"available": False})
        assert "HYBRID" not in html

    def test_returns_html_string_when_unavailable(self):
        html = build_memory_evidence_html({"available": False})
        assert isinstance(html, str)
        assert "<" in html
