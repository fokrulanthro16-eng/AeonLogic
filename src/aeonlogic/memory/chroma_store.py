from __future__ import annotations

from typing import Any

import chromadb

from .schemas import Lesson


class ChromaMemoryStore:
    def __init__(
        self,
        path: str = ".chroma_db",
        collection_name: str = "lessons",
        _client: Any = None,
    ) -> None:
        self._collection_name = collection_name
        self._client = _client if _client is not None else chromadb.PersistentClient(path=path)
        self._collection = self._client.get_or_create_collection(collection_name)

    # ------------------------------------------------------------------
    def write_lesson(self, lesson: Lesson) -> str:
        meta: dict[str, Any] = {"source": lesson.source, "timestamp": lesson.timestamp}
        meta.update(lesson.metadata)
        self._collection.add(
            documents=[lesson.content],
            metadatas=[meta],
            ids=[lesson.id],
        )
        return lesson.id

    def search_lessons(self, query: str, n_results: int = 5) -> list[Lesson]:
        count = self._collection.count()
        if count == 0:
            return []
        actual_n = min(n_results, count)
        results = self._collection.query(query_texts=[query], n_results=actual_n)
        lessons: list[Lesson] = []
        for doc, meta, lid in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["ids"][0],
        ):
            m = dict(meta)
            source = m.pop("source", "")
            timestamp = m.pop("timestamp", "")
            lessons.append(Lesson(id=lid, content=doc, source=source, timestamp=timestamp, metadata=m))
        return lessons

    def clear(self) -> None:
        self._client.delete_collection(self._collection_name)
        self._collection = self._client.get_or_create_collection(self._collection_name)
