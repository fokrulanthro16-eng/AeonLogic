from __future__ import annotations

from typing import Any

from .schemas import FailureLesson, Lesson, SuccessLesson


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
    """
    Coordinates semantic memory (Chroma/Mock) and graph memory (Neo4j).

    Chroma is authoritative: writes always succeed via the Chroma-or-Mock
    fallback chain.  Neo4j is best-effort: its failures are silently swallowed
    so the pipeline is never interrupted.
    """

    def __init__(
        self,
        path: str = ".chroma_db",
        collection_name: str = "lessons",
        _client: Any = None,
        _neo4j: Any = None,
    ) -> None:
        self._store = _build_store(path=path, collection_name=collection_name, _client=_client)
        self._neo4j = _neo4j  # Neo4jMemoryStore or None

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def backend(self) -> str:
        return type(self._store).__name__

    @property
    def neo4j_available(self) -> bool:
        return self._neo4j is not None and bool(getattr(self._neo4j, "is_available", False))

    # ------------------------------------------------------------------
    # Existing lesson write (backward-compatible)
    # ------------------------------------------------------------------

    def write_lesson(self, lesson: Lesson) -> str:
        return self._store.write_lesson(lesson)

    # ------------------------------------------------------------------
    # Typed lesson writes  (Chroma authoritative + Neo4j best-effort)
    # ------------------------------------------------------------------

    def write_failure_lesson(self, lesson: FailureLesson) -> str:
        """Write failure lesson to Chroma then attempt Neo4j (never raises)."""
        chroma_lesson = Lesson(
            id=lesson.id,
            content=f"[failure] {lesson.task_description}: {lesson.failure_reason}",
            source="failure",
            timestamp=lesson.timestamp,
            metadata={
                "task_description": lesson.task_description,
                "artifact_id": lesson.artifact_id,
            },
        )
        lid = lesson.id
        try:
            lid = self._store.write_lesson(chroma_lesson)
        except Exception:
            pass  # chroma failed mid-op; return the id anyway
        try:
            if self._neo4j is not None:
                self._neo4j.write_failure_lesson(lesson)
        except Exception:
            pass
        return lid

    def write_success_lesson(self, lesson: SuccessLesson) -> str:
        """Write success lesson to Chroma then attempt Neo4j (never raises)."""
        chroma_lesson = Lesson(
            id=lesson.id,
            content=f"[success] {lesson.task_description}: {lesson.success_summary}",
            source="success",
            timestamp=lesson.timestamp,
            metadata={
                "task_description": lesson.task_description,
                "artifact_id": lesson.artifact_id,
            },
        )
        lid = lesson.id
        try:
            lid = self._store.write_lesson(chroma_lesson)
        except Exception:
            pass
        try:
            if self._neo4j is not None:
                self._neo4j.write_success_lesson(lesson)
        except Exception:
            pass
        return lid

    # ------------------------------------------------------------------
    # Search (Chroma-backed)
    # ------------------------------------------------------------------

    def search_lessons(self, query: str, n_results: int = 5) -> list[Lesson]:
        return self._store.search_lessons(query, n_results)

    def clear(self) -> None:
        self._store.clear()
