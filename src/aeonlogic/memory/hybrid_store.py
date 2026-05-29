from __future__ import annotations

from typing import Any

from .schemas import Lesson


class MockMemoryStore:
    """In-memory fallback used when chromadb is unavailable."""

    def __init__(self) -> None:
        self._store: dict[str, Lesson] = {}

    def write_lesson(self, lesson: Lesson) -> str:
        self._store[lesson.id] = lesson
        return lesson.id

    def search_lessons(self, query: str, n_results: int = 5) -> list[Lesson]:
        q = query.lower()
        hits = [l for l in self._store.values() if q in l.content.lower()]
        return hits[:n_results]

    def clear(self) -> None:
        self._store.clear()


def _build_store(path: str, collection_name: str, _client: Any = None) -> Any:
    try:
        from .chroma_store import ChromaMemoryStore
        return ChromaMemoryStore(path=path, collection_name=collection_name, _client=_client)
    except Exception:
        return MockMemoryStore()


class HybridMemoryStore:
    def __init__(
        self,
        path: str = ".chroma_db",
        collection_name: str = "lessons",
        _client: Any = None,
    ) -> None:
        self._store = _build_store(path=path, collection_name=collection_name, _client=_client)

    @property
    def backend(self) -> str:
        return type(self._store).__name__

    def write_lesson(self, lesson: Lesson) -> str:
        return self._store.write_lesson(lesson)

    def search_lessons(self, query: str, n_results: int = 5) -> list[Lesson]:
        return self._store.search_lessons(query, n_results)

    def clear(self) -> None:
        self._store.clear()
