from __future__ import annotations

from typing import Any, Protocol

_HINT_HEADER = "Relevant past lessons:"


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


def summarize_lessons(lessons: list[Any], max_lessons: int = 5) -> str:
    """Convert a list of Lesson objects into a compact prompt hint.

    Returns an empty string when lessons is empty so callers can guard with
    ``if memory_hint:`` to leave the base prompt completely unchanged.
    """
    if not lessons:
        return ""
    lines = [_HINT_HEADER]
    for lesson in lessons[:max_lessons]:
        lines.append(f"  [{lesson.source}] {lesson.content}")
    return "\n".join(lines)
