"""Phase 4A: ChromaDB persistent memory — unit tests."""
import pytest

chromadb = pytest.importorskip("chromadb")

from aeonlogic.memory.schemas import Lesson
from aeonlogic.memory.chroma_store import ChromaMemoryStore
from aeonlogic.memory.hybrid_store import HybridMemoryStore, MockMemoryStore


import uuid as _uuid


@pytest.fixture()
def store() -> ChromaMemoryStore:
    """Ephemeral ChromaDB store with a unique collection per test to prevent state leakage."""
    return ChromaMemoryStore(
        _client=chromadb.EphemeralClient(),
        collection_name=f"test_{_uuid.uuid4().hex}",
    )


# ---------------------------------------------------------------------------
# ChromaMemoryStore tests
# ---------------------------------------------------------------------------

def test_write_returns_id(store: ChromaMemoryStore) -> None:
    lesson = Lesson(content="retry on transient errors", source="agent")
    lid = store.write_lesson(lesson)
    assert lid == lesson.id


def test_search_finds_written_lesson(store: ChromaMemoryStore) -> None:
    store.write_lesson(Lesson(content="always validate inputs before processing"))
    results = store.search_lessons("validate inputs")
    assert len(results) == 1
    assert "validate" in results[0].content


def test_search_returns_empty_when_no_lessons(store: ChromaMemoryStore) -> None:
    assert store.search_lessons("anything") == []


def test_search_respects_n_results(store: ChromaMemoryStore) -> None:
    for i in range(6):
        store.write_lesson(Lesson(content=f"lesson about topic {i}"))
    results = store.search_lessons("lesson topic", n_results=3)
    assert len(results) <= 3


def test_search_preserves_source_and_metadata(store: ChromaMemoryStore) -> None:
    lesson = Lesson(
        content="use exponential backoff",
        source="user",
        timestamp="2026-05-29T00:00:00",
        metadata={"priority": "high"},
    )
    store.write_lesson(lesson)
    results = store.search_lessons("exponential backoff")
    assert results[0].source == "user"
    assert results[0].timestamp == "2026-05-29T00:00:00"
    assert results[0].metadata.get("priority") == "high"


def test_clear_removes_all_lessons(store: ChromaMemoryStore) -> None:
    store.write_lesson(Lesson(content="lesson one"))
    store.write_lesson(Lesson(content="lesson two"))
    store.clear()
    assert store.search_lessons("lesson") == []


def test_clear_then_write(store: ChromaMemoryStore) -> None:
    store.write_lesson(Lesson(content="old lesson"))
    store.clear()
    store.write_lesson(Lesson(content="new lesson after clear"))
    results = store.search_lessons("new lesson")
    assert len(results) == 1


# ---------------------------------------------------------------------------
# MockMemoryStore (fallback) tests
# ---------------------------------------------------------------------------

def test_mock_write_and_search() -> None:
    mock = MockMemoryStore()
    mock.write_lesson(Lesson(content="fallback lesson content"))
    results = mock.search_lessons("fallback")
    assert len(results) == 1


def test_mock_clear() -> None:
    mock = MockMemoryStore()
    mock.write_lesson(Lesson(content="will be cleared"))
    mock.clear()
    assert mock.search_lessons("cleared") == []


def test_mock_search_empty() -> None:
    mock = MockMemoryStore()
    assert mock.search_lessons("nothing") == []


# ---------------------------------------------------------------------------
# HybridMemoryStore tests
# ---------------------------------------------------------------------------

def test_hybrid_uses_chroma_when_available() -> None:
    hybrid = HybridMemoryStore(_client=chromadb.EphemeralClient(), collection_name=f"test_{_uuid.uuid4().hex}")
    assert hybrid.backend == "ChromaMemoryStore"


def test_hybrid_falls_back_to_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    import aeonlogic.memory.hybrid_store as hs

    original = hs._build_store

    def _fail(*args, **kwargs):  # noqa: ANN001
        return MockMemoryStore()

    monkeypatch.setattr(hs, "_build_store", _fail)
    hybrid = HybridMemoryStore()
    assert hybrid.backend == "MockMemoryStore"

    hs._build_store = original  # restore (monkeypatch also does this on teardown)


def test_hybrid_write_and_search() -> None:
    hybrid = HybridMemoryStore(_client=chromadb.EphemeralClient(), collection_name=f"test_{_uuid.uuid4().hex}")
    hybrid.write_lesson(Lesson(content="hybrid test lesson"))
    results = hybrid.search_lessons("hybrid test")
    assert len(results) == 1


def test_hybrid_clear() -> None:
    hybrid = HybridMemoryStore(_client=chromadb.EphemeralClient(), collection_name=f"test_{_uuid.uuid4().hex}")
    hybrid.write_lesson(Lesson(content="to be cleared via hybrid"))
    hybrid.clear()
    assert hybrid.search_lessons("cleared") == []
