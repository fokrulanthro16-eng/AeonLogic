from __future__ import annotations

from typing import Any, Protocol


class _MemoryBackend(Protocol):
    def search_lessons(self, query: str, n_results: int = 5) -> list[Any]: ...


class MemoryRetriever:
    def __init__(self, store: _MemoryBackend) -> None:
        self._store = store

    def retrieve_similar_lessons(self, query: str, limit: int = 5) -> list[Any]:
        if not query or not query.strip():
            return []
        try:
            return self._store.search_lessons(query, n_results=limit)
        except Exception:
            return []
