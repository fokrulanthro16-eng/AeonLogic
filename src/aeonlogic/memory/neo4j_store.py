from __future__ import annotations

from typing import Any

from aeonlogic.config.settings import get_settings
from aeonlogic.memory.schemas import ArtifactRelationship, FailureLesson, SuccessLesson


class Neo4jMemoryStore:
    """
    Knowledge-graph store for lessons and artifact relationships.

    The ``neo4j`` package is imported lazily so the module loads even when
    the driver is not installed.  All public methods degrade gracefully to
    safe no-ops when the store is unavailable (no URI configured, driver
    import fails, or server unreachable).

    Inject ``_driver`` in tests to bypass real connectivity entirely.
    """

    def __init__(
        self,
        uri: str | None = None,
        username: str | None = None,
        password: str | None = None,
        _driver: Any = None,
    ) -> None:
        settings = get_settings()
        self._uri: str = uri if uri is not None else settings.neo4j_uri
        self._username: str = username if username is not None else settings.neo4j_username
        self._password: str = password if password is not None else settings.neo4j_password
        self._driver: Any = _driver
        self._available: bool = _driver is not None

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Open (or verify) the driver connection.  Returns True on success."""
        if self._driver is not None:
            try:
                self._driver.verify_connectivity()
                self._available = True
                return True
            except Exception:
                self._available = False
                return False
        if not self._uri:
            self._available = False
            return False
        try:
            from neo4j import GraphDatabase  # lazy — optional dependency
            self._driver = GraphDatabase.driver(
                self._uri,
                auth=(self._username, self._password),
            )
            self._driver.verify_connectivity()
            self._available = True
            return True
        except Exception:
            self._driver = None
            self._available = False
            return False

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def write_failure_lesson(self, lesson: FailureLesson) -> str | None:
        """Persist a FailureLesson node.  Returns the lesson id or None."""
        if not self._available or self._driver is None:
            return None
        try:
            self._driver.execute_query(
                "MERGE (n:FailureLesson {id: $id}) "
                "SET n.task_description = $task_description, "
                "    n.failure_reason   = $failure_reason, "
                "    n.artifact_id      = $artifact_id, "
                "    n.timestamp        = $timestamp "
                "RETURN n.id AS id",
                id=lesson.id,
                task_description=lesson.task_description,
                failure_reason=lesson.failure_reason,
                artifact_id=lesson.artifact_id,
                timestamp=lesson.timestamp,
            )
            return lesson.id
        except Exception:
            self._available = False
            return None

    def write_success_lesson(self, lesson: SuccessLesson) -> str | None:
        """Persist a SuccessLesson node.  Returns the lesson id or None."""
        if not self._available or self._driver is None:
            return None
        try:
            self._driver.execute_query(
                "MERGE (n:SuccessLesson {id: $id}) "
                "SET n.task_description = $task_description, "
                "    n.success_summary  = $success_summary, "
                "    n.artifact_id      = $artifact_id, "
                "    n.timestamp        = $timestamp "
                "RETURN n.id AS id",
                id=lesson.id,
                task_description=lesson.task_description,
                success_summary=lesson.success_summary,
                artifact_id=lesson.artifact_id,
                timestamp=lesson.timestamp,
            )
            return lesson.id
        except Exception:
            self._available = False
            return None

    def write_artifact_relationship(self, rel: ArtifactRelationship) -> bool:
        """Merge Artifact→Task and Artifact→Lesson edges.  Returns True on success."""
        if not self._available or self._driver is None:
            return False
        try:
            self._driver.execute_query(
                "MERGE (a:Artifact {id: $artifact_id}) "
                "MERGE (t:Task     {id: $task_id}) "
                "MERGE (l:Lesson   {id: $lesson_id}) "
                "MERGE (a)-[:DERIVED_FROM]->(t) "
                "MERGE (a)-[r:IMPROVED_BY {type: $relationship_type}]->(l) "
                "RETURN a.id AS artifact_id",
                artifact_id=rel.artifact_id,
                task_id=rel.task_id,
                lesson_id=rel.lesson_id,
                relationship_type=rel.relationship_type,
            )
            return True
        except Exception:
            self._available = False
            return False

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Return True if the driver is reachable."""
        if not self._available or self._driver is None:
            return False
        try:
            self._driver.execute_query("RETURN 1 AS ok")
            return True
        except Exception:
            self._available = False
            return False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the driver connection gracefully."""
        if self._driver is not None:
            try:
                self._driver.close()
            except Exception:
                pass
        self._driver = None
        self._available = False

    @property
    def is_available(self) -> bool:
        return self._available
