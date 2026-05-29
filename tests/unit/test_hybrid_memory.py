"""Phase 4E: HybridMemoryStore orchestration — unit tests."""
from __future__ import annotations

import uuid
from typing import Any

import pytest

chromadb = pytest.importorskip("chromadb")

from aeonlogic.memory.hybrid_store import HybridMemoryStore, MockMemoryStore
from aeonlogic.memory.neo4j_store import Neo4jMemoryStore
from aeonlogic.memory.schemas import FailureLesson, Lesson, SuccessLesson


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------

class _MockNeo4jDriver:
    def __init__(self, raise_on_query: bool = False) -> None:
        self._raise = raise_on_query
        self.queries: list[str] = []

    def execute_query(self, query: str, **kwargs: Any) -> None:
        if self._raise:
            raise RuntimeError("Neo4j query failed")
        self.queries.append(query)

    def verify_connectivity(self) -> None:
        pass

    def close(self) -> None:
        pass


class _FailingChromaClient:
    """Simulates Chroma being completely unavailable at init time."""

    def get_or_create_collection(self, name: str) -> None:
        raise RuntimeError("Chroma service unavailable")


class _FailingWriteStore:
    """Simulates a store that fails on every write (mid-operation failure)."""

    def write_lesson(self, lesson: Lesson) -> str:
        raise RuntimeError("Storage write failed")

    def search_lessons(self, query: str, n_results: int = 5) -> list[Lesson]:
        return []

    def clear(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _col() -> str:
    return f"test_{uuid.uuid4().hex}"


def _ephemeral_chroma() -> Any:
    return chromadb.EphemeralClient()


@pytest.fixture()
def neo4j_driver() -> _MockNeo4jDriver:
    return _MockNeo4jDriver()


@pytest.fixture()
def neo4j_store(neo4j_driver: _MockNeo4jDriver) -> Neo4jMemoryStore:
    return Neo4jMemoryStore(_driver=neo4j_driver)


@pytest.fixture()
def hybrid_both(neo4j_store: Neo4jMemoryStore) -> HybridMemoryStore:
    """Both Chroma and Neo4j available."""
    return HybridMemoryStore(
        _client=_ephemeral_chroma(),
        collection_name=_col(),
        _neo4j=neo4j_store,
    )


@pytest.fixture()
def hybrid_chroma_only() -> HybridMemoryStore:
    """Chroma available, no Neo4j."""
    return HybridMemoryStore(
        _client=_ephemeral_chroma(),
        collection_name=_col(),
    )


# ---------------------------------------------------------------------------
# Backend introspection
# ---------------------------------------------------------------------------

def test_chroma_backend_label(hybrid_both: HybridMemoryStore) -> None:
    assert hybrid_both.backend == "ChromaMemoryStore"


def test_neo4j_available_true_when_driver_present(hybrid_both: HybridMemoryStore) -> None:
    assert hybrid_both.neo4j_available is True


def test_neo4j_available_false_when_no_neo4j(hybrid_chroma_only: HybridMemoryStore) -> None:
    assert hybrid_chroma_only.neo4j_available is False


def test_neo4j_available_false_when_driver_unavailable() -> None:
    broken_driver = _MockNeo4jDriver()
    store = Neo4jMemoryStore(_driver=broken_driver)
    store.close()  # marks as unavailable
    hybrid = HybridMemoryStore(_client=_ephemeral_chroma(), collection_name=_col(), _neo4j=store)
    assert hybrid.neo4j_available is False


def test_chroma_unavailable_falls_back_to_mock() -> None:
    hybrid = HybridMemoryStore(_client=_FailingChromaClient(), collection_name=_col())
    assert hybrid.backend == "MockMemoryStore"


# ---------------------------------------------------------------------------
# write_failure_lesson — both backends available
# ---------------------------------------------------------------------------

def test_write_failure_lesson_returns_id(hybrid_both: HybridMemoryStore) -> None:
    lesson = FailureLesson(task_description="auth module", failure_reason="null pointer")
    lid = hybrid_both.write_failure_lesson(lesson)
    assert lid == lesson.id


def test_write_failure_lesson_sends_to_neo4j(
    hybrid_both: HybridMemoryStore, neo4j_driver: _MockNeo4jDriver
) -> None:
    lesson = FailureLesson(task_description="auth module", failure_reason="null pointer")
    hybrid_both.write_failure_lesson(lesson)
    assert any("FailureLesson" in q for q in neo4j_driver.queries)


def test_write_failure_lesson_content_in_chroma(hybrid_both: HybridMemoryStore) -> None:
    lesson = FailureLesson(
        task_description="auth module",
        failure_reason="null pointer in JWT handler",
    )
    hybrid_both.write_failure_lesson(lesson)
    results = hybrid_both.search_lessons("null pointer JWT")
    assert len(results) >= 1
    assert any("null pointer" in r.content for r in results)


def test_write_failure_lesson_source_is_failure(hybrid_both: HybridMemoryStore) -> None:
    lesson = FailureLesson(task_description="auth", failure_reason="token expired")
    hybrid_both.write_failure_lesson(lesson)
    results = hybrid_both.search_lessons("token expired")
    assert results[0].source == "failure"


# ---------------------------------------------------------------------------
# write_success_lesson — both backends available
# ---------------------------------------------------------------------------

def test_write_success_lesson_returns_id(hybrid_both: HybridMemoryStore) -> None:
    lesson = SuccessLesson(task_description="auth module", success_summary="all tests passed")
    lid = hybrid_both.write_success_lesson(lesson)
    assert lid == lesson.id


def test_write_success_lesson_sends_to_neo4j(
    hybrid_both: HybridMemoryStore, neo4j_driver: _MockNeo4jDriver
) -> None:
    lesson = SuccessLesson(task_description="auth module", success_summary="all tests passed")
    hybrid_both.write_success_lesson(lesson)
    assert any("SuccessLesson" in q for q in neo4j_driver.queries)


def test_write_success_lesson_content_in_chroma(hybrid_both: HybridMemoryStore) -> None:
    lesson = SuccessLesson(
        task_description="auth module",
        success_summary="bcrypt hashing with PBKDF2 fallback",
    )
    hybrid_both.write_success_lesson(lesson)
    results = hybrid_both.search_lessons("bcrypt hashing")
    assert len(results) >= 1
    assert any("bcrypt" in r.content for r in results)


def test_write_success_lesson_source_is_success(hybrid_both: HybridMemoryStore) -> None:
    lesson = SuccessLesson(task_description="auth", success_summary="JWT validated correctly")
    hybrid_both.write_success_lesson(lesson)
    results = hybrid_both.search_lessons("JWT validated")
    assert results[0].source == "success"


# ---------------------------------------------------------------------------
# Chroma-only — no Neo4j
# ---------------------------------------------------------------------------

def test_write_failure_lesson_no_neo4j_returns_id(hybrid_chroma_only: HybridMemoryStore) -> None:
    lesson = FailureLesson(task_description="auth", failure_reason="timeout")
    lid = hybrid_chroma_only.write_failure_lesson(lesson)
    assert lid == lesson.id


def test_write_success_lesson_no_neo4j_returns_id(hybrid_chroma_only: HybridMemoryStore) -> None:
    lesson = SuccessLesson(task_description="auth", success_summary="ok")
    lid = hybrid_chroma_only.write_success_lesson(lesson)
    assert lid == lesson.id


def test_no_neo4j_write_failure_still_searchable(hybrid_chroma_only: HybridMemoryStore) -> None:
    lesson = FailureLesson(task_description="auth", failure_reason="missing rate limit")
    hybrid_chroma_only.write_failure_lesson(lesson)
    results = hybrid_chroma_only.search_lessons("rate limit")
    assert len(results) >= 1


# ---------------------------------------------------------------------------
# Neo4j raises — must never propagate
# ---------------------------------------------------------------------------

def test_write_failure_lesson_neo4j_exception_does_not_raise() -> None:
    broken_driver = _MockNeo4jDriver(raise_on_query=True)
    neo4j = Neo4jMemoryStore(_driver=broken_driver)
    hybrid = HybridMemoryStore(
        _client=_ephemeral_chroma(), collection_name=_col(), _neo4j=neo4j
    )
    lesson = FailureLesson(task_description="t", failure_reason="r")
    lid = hybrid.write_failure_lesson(lesson)  # must not raise
    assert lid == lesson.id


def test_write_success_lesson_neo4j_exception_does_not_raise() -> None:
    broken_driver = _MockNeo4jDriver(raise_on_query=True)
    neo4j = Neo4jMemoryStore(_driver=broken_driver)
    hybrid = HybridMemoryStore(
        _client=_ephemeral_chroma(), collection_name=_col(), _neo4j=neo4j
    )
    lesson = SuccessLesson(task_description="t", success_summary="s")
    lid = hybrid.write_success_lesson(lesson)  # must not raise
    assert lid == lesson.id


# ---------------------------------------------------------------------------
# Chroma falls back to Mock — both typed writes still work
# ---------------------------------------------------------------------------

def test_mock_fallback_write_failure_lesson_works() -> None:
    hybrid = HybridMemoryStore(_client=_FailingChromaClient(), collection_name=_col())
    assert hybrid.backend == "MockMemoryStore"
    lesson = FailureLesson(task_description="auth", failure_reason="bad token")
    lid = hybrid.write_failure_lesson(lesson)
    assert lid == lesson.id


def test_mock_fallback_write_success_lesson_works() -> None:
    hybrid = HybridMemoryStore(_client=_FailingChromaClient(), collection_name=_col())
    lesson = SuccessLesson(task_description="auth", success_summary="works fine")
    lid = hybrid.write_success_lesson(lesson)
    assert lid == lesson.id


def test_mock_fallback_search_returns_written_failure_lesson() -> None:
    hybrid = HybridMemoryStore(_client=_FailingChromaClient(), collection_name=_col())
    lesson = FailureLesson(task_description="auth", failure_reason="missing validation")
    hybrid.write_failure_lesson(lesson)
    results = hybrid.search_lessons("missing validation")
    assert len(results) == 1


def test_mock_fallback_search_returns_written_success_lesson() -> None:
    hybrid = HybridMemoryStore(_client=_FailingChromaClient(), collection_name=_col())
    lesson = SuccessLesson(task_description="auth", success_summary="validation passed")
    hybrid.write_success_lesson(lesson)
    results = hybrid.search_lessons("validation passed")
    assert len(results) == 1


# ---------------------------------------------------------------------------
# Both backends broken — write_* must never raise
# ---------------------------------------------------------------------------

def test_write_never_raises_when_both_backends_fail() -> None:
    hybrid = HybridMemoryStore(
        _client=_ephemeral_chroma(), collection_name=_col(),
        _neo4j=Neo4jMemoryStore(_driver=_MockNeo4jDriver(raise_on_query=True)),
    )
    hybrid._store = _FailingWriteStore()  # force Chroma write to fail
    lesson_f = FailureLesson(task_description="t", failure_reason="r")
    lesson_s = SuccessLesson(task_description="t", success_summary="s")
    hybrid.write_failure_lesson(lesson_f)  # must not raise
    hybrid.write_success_lesson(lesson_s)  # must not raise


# ---------------------------------------------------------------------------
# search_lessons reads from Chroma
# ---------------------------------------------------------------------------

def test_search_returns_failure_lessons(hybrid_both: HybridMemoryStore) -> None:
    f = FailureLesson(task_description="auth", failure_reason="SQL injection risk")
    hybrid_both.write_failure_lesson(f)
    results = hybrid_both.search_lessons("SQL injection")
    assert any("SQL injection" in r.content for r in results)


def test_search_returns_success_lessons(hybrid_both: HybridMemoryStore) -> None:
    s = SuccessLesson(task_description="auth", success_summary="parameterized queries used")
    hybrid_both.write_success_lesson(s)
    results = hybrid_both.search_lessons("parameterized queries")
    assert any("parameterized" in r.content for r in results)


def test_search_returns_lesson_objects(hybrid_both: HybridMemoryStore) -> None:
    hybrid_both.write_failure_lesson(FailureLesson(task_description="t", failure_reason="err"))
    results = hybrid_both.search_lessons("err")
    for r in results:
        assert isinstance(r, Lesson)


def test_search_empty_store_returns_empty_list(hybrid_both: HybridMemoryStore) -> None:
    assert hybrid_both.search_lessons("anything") == []


# ---------------------------------------------------------------------------
# Backward compatibility — existing write_lesson / clear still work
# ---------------------------------------------------------------------------

def test_existing_write_lesson_unaffected(hybrid_both: HybridMemoryStore) -> None:
    lesson = Lesson(content="legacy lesson content", source="agent")
    lid = hybrid_both.write_lesson(lesson)
    assert lid == lesson.id


def test_existing_write_lesson_searchable(hybrid_both: HybridMemoryStore) -> None:
    lesson = Lesson(content="legacy lesson about rate limiting", source="agent")
    hybrid_both.write_lesson(lesson)
    results = hybrid_both.search_lessons("rate limiting")
    assert len(results) >= 1


def test_clear_removes_all_written_lessons(hybrid_both: HybridMemoryStore) -> None:
    hybrid_both.write_failure_lesson(FailureLesson(task_description="t", failure_reason="r"))
    hybrid_both.write_success_lesson(SuccessLesson(task_description="t", success_summary="s"))
    hybrid_both.clear()
    assert hybrid_both.search_lessons("failure") == []
    assert hybrid_both.search_lessons("success") == []
