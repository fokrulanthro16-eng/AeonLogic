"""Phase 4B: MemoryRetriever — unit tests."""
import uuid

import pytest

chromadb = pytest.importorskip("chromadb")

from aeonlogic.memory.schemas import Lesson
from aeonlogic.memory.chroma_store import ChromaMemoryStore
from aeonlogic.memory.hybrid_store import HybridMemoryStore, MockMemoryStore
from aeonlogic.memory.retrieval import MemoryRetriever


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ephemeral_store() -> ChromaMemoryStore:
    return ChromaMemoryStore(
        _client=chromadb.EphemeralClient(),
        collection_name=f"test_{uuid.uuid4().hex}",
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def retriever_with_lessons() -> MemoryRetriever:
    store = _ephemeral_store()
    store.write_lesson(Lesson(
        content="null pointer exception caused agent crash during tool call",
        source="failure",
        metadata={"outcome": "failure"},
    ))
    store.write_lesson(Lesson(
        content="retry with exponential backoff resolved transient network error",
        source="success",
        metadata={"outcome": "success"},
    ))
    store.write_lesson(Lesson(
        content="task completed: code generated and all tests passed on first attempt",
        source="success",
        metadata={"outcome": "success"},
    ))
    return MemoryRetriever(store)


# ---------------------------------------------------------------------------
# Core retrieval tests
# ---------------------------------------------------------------------------

def test_retrieve_relevant_failure_lessons(retriever_with_lessons: MemoryRetriever) -> None:
    results = retriever_with_lessons.retrieve_similar_lessons("agent crash exception error")
    assert len(results) >= 1
    contents = [r.content for r in results]
    assert any("exception" in c or "crash" in c for c in contents)


def test_retrieve_relevant_success_lessons(retriever_with_lessons: MemoryRetriever) -> None:
    results = retriever_with_lessons.retrieve_similar_lessons("tests passed code generation success")
    assert len(results) >= 1
    contents = [r.content for r in results]
    assert any("test" in c or "success" in c or "completed" in c for c in contents)


def test_retrieve_respects_limit(retriever_with_lessons: MemoryRetriever) -> None:
    results = retriever_with_lessons.retrieve_similar_lessons("agent task", limit=1)
    assert len(results) == 1


def test_retrieve_returns_lesson_objects(retriever_with_lessons: MemoryRetriever) -> None:
    results = retriever_with_lessons.retrieve_similar_lessons("error")
    for r in results:
        assert isinstance(r, Lesson)
        assert r.id
        assert r.content


def test_retrieve_preserves_source(retriever_with_lessons: MemoryRetriever) -> None:
    results = retriever_with_lessons.retrieve_similar_lessons("null pointer exception crash")
    assert any(r.source == "failure" for r in results)


# ---------------------------------------------------------------------------
# Empty query
# ---------------------------------------------------------------------------

def test_empty_query_returns_empty_list(retriever_with_lessons: MemoryRetriever) -> None:
    assert retriever_with_lessons.retrieve_similar_lessons("") == []


def test_whitespace_query_returns_empty_list(retriever_with_lessons: MemoryRetriever) -> None:
    assert retriever_with_lessons.retrieve_similar_lessons("   ") == []


# ---------------------------------------------------------------------------
# Backend failure safety
# ---------------------------------------------------------------------------

class _BrokenStore:
    def search_lessons(self, query: str, n_results: int = 5) -> list[Lesson]:
        raise RuntimeError("database unavailable")


def test_backend_failure_returns_empty_list() -> None:
    retriever = MemoryRetriever(_BrokenStore())
    result = retriever.retrieve_similar_lessons("any query")
    assert result == []


def test_backend_exception_does_not_propagate() -> None:
    retriever = MemoryRetriever(_BrokenStore())
    try:
        retriever.retrieve_similar_lessons("query")
    except Exception as exc:
        pytest.fail(f"Exception leaked from retriever: {exc}")


# ---------------------------------------------------------------------------
# MockMemoryStore backend (no chromadb needed)
# ---------------------------------------------------------------------------

def test_retriever_works_with_mock_backend() -> None:
    store = MockMemoryStore()
    store.write_lesson(Lesson(content="retry timeout resolves transient errors", source="success"))
    retriever = MemoryRetriever(store)
    results = retriever.retrieve_similar_lessons("retry timeout")
    assert len(results) == 1
    assert results[0].source == "success"


def test_retriever_empty_mock_backend() -> None:
    retriever = MemoryRetriever(MockMemoryStore())
    assert retriever.retrieve_similar_lessons("anything") == []


# ---------------------------------------------------------------------------
# HybridMemoryStore integration
# ---------------------------------------------------------------------------

def test_retriever_with_hybrid_store() -> None:
    store = HybridMemoryStore(
        _client=chromadb.EphemeralClient(),
        collection_name=f"test_{uuid.uuid4().hex}",
    )
    store.write_lesson(Lesson(content="validation error caught before execution"))
    retriever = MemoryRetriever(store)
    results = retriever.retrieve_similar_lessons("validation error")
    assert len(results) == 1
