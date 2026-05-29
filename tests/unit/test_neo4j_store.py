"""Phase 4D: Neo4j knowledge-graph store — unit tests (no real server required)."""
from __future__ import annotations

import sys
from typing import Any

import pytest

from aeonlogic.config.settings import reset_settings
from aeonlogic.memory.neo4j_store import Neo4jMemoryStore
from aeonlogic.memory.schemas import ArtifactRelationship, FailureLesson, SuccessLesson


# ---------------------------------------------------------------------------
# Mock driver — records every execute_query call, can simulate failures
# ---------------------------------------------------------------------------

class _MockNeo4jDriver:
    def __init__(self, raise_on_query: bool = False, raise_on_verify: bool = False) -> None:
        self._raise_query = raise_on_query
        self._raise_verify = raise_on_verify
        self.queries: list[str] = []
        self.kwargs_log: list[dict[str, Any]] = []

    def execute_query(self, query: str, **kwargs: Any) -> None:
        if self._raise_query:
            raise RuntimeError("Neo4j query failed")
        self.queries.append(query)
        self.kwargs_log.append(kwargs)

    def verify_connectivity(self) -> None:
        if self._raise_verify:
            raise RuntimeError("Cannot reach Neo4j")

    def close(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_settings() -> None:
    reset_settings()
    yield
    reset_settings()


@pytest.fixture()
def driver() -> _MockNeo4jDriver:
    return _MockNeo4jDriver()


@pytest.fixture()
def store(driver: _MockNeo4jDriver) -> Neo4jMemoryStore:
    return Neo4jMemoryStore(_driver=driver)


# ---------------------------------------------------------------------------
# Schema dataclasses
# ---------------------------------------------------------------------------

def test_failure_lesson_has_auto_id() -> None:
    lesson = FailureLesson(task_description="auth task", failure_reason="null pointer")
    assert lesson.id
    assert lesson.task_description == "auth task"
    assert lesson.failure_reason == "null pointer"


def test_success_lesson_has_auto_id() -> None:
    lesson = SuccessLesson(task_description="auth task", success_summary="all tests passed")
    assert lesson.id
    assert lesson.success_summary == "all tests passed"


def test_artifact_relationship_defaults() -> None:
    rel = ArtifactRelationship(artifact_id="a1", task_id="t1", lesson_id="l1")
    assert rel.relationship_type == "IMPROVED_BY"


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def test_settings_has_neo4j_uri_field() -> None:
    from aeonlogic.config.settings import get_settings
    s = get_settings()
    assert hasattr(s, "neo4j_uri")
    assert isinstance(s.neo4j_uri, str)


def test_settings_has_neo4j_username_field() -> None:
    from aeonlogic.config.settings import get_settings
    s = get_settings()
    assert hasattr(s, "neo4j_username")
    assert s.neo4j_username == "neo4j"  # default


def test_settings_has_neo4j_password_field() -> None:
    from aeonlogic.config.settings import get_settings
    s = get_settings()
    assert hasattr(s, "neo4j_password")
    assert isinstance(s.neo4j_password, str)


# ---------------------------------------------------------------------------
# connect()
# ---------------------------------------------------------------------------

def test_connect_with_injected_driver_returns_true(store: Neo4jMemoryStore) -> None:
    assert store.connect() is True


def test_connect_marks_store_available(store: Neo4jMemoryStore) -> None:
    store.connect()
    assert store.is_available is True


def test_connect_with_empty_uri_returns_false() -> None:
    store = Neo4jMemoryStore(uri="")
    assert store.connect() is False
    assert store.is_available is False


def test_connect_fails_gracefully_when_neo4j_not_importable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "neo4j", None)  # type: ignore[arg-type]
    store = Neo4jMemoryStore(uri="bolt://localhost:7687", username="neo4j", password="test")
    result = store.connect()
    assert result is False
    assert store.is_available is False


def test_connect_fails_when_verify_connectivity_raises() -> None:
    broken_driver = _MockNeo4jDriver(raise_on_verify=True)
    store = Neo4jMemoryStore(_driver=broken_driver)
    # _driver is injected so _available starts True; connect() re-verifies
    result = store.connect()
    assert result is False
    assert store.is_available is False


def test_connect_uses_credentials_from_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NEO4J_URI", "bolt://test-host:7687")
    monkeypatch.setenv("NEO4J_USERNAME", "admin")
    monkeypatch.setenv("NEO4J_PASSWORD", "secret")
    reset_settings()
    store = Neo4jMemoryStore()
    assert store._uri == "bolt://test-host:7687"
    assert store._username == "admin"
    assert store._password == "secret"


# ---------------------------------------------------------------------------
# health_check()
# ---------------------------------------------------------------------------

def test_health_check_with_available_store(store: Neo4jMemoryStore) -> None:
    assert store.health_check() is True


def test_health_check_without_driver_returns_false() -> None:
    store = Neo4jMemoryStore()  # no driver, not connected
    assert store.health_check() is False


def test_health_check_marks_unavailable_on_exception() -> None:
    broken = _MockNeo4jDriver(raise_on_query=True)
    store = Neo4jMemoryStore(_driver=broken)
    assert store.health_check() is False
    assert store.is_available is False


def test_health_check_executes_ping_query(store: Neo4jMemoryStore, driver: _MockNeo4jDriver) -> None:
    store.health_check()
    assert any("RETURN 1" in q for q in driver.queries)


# ---------------------------------------------------------------------------
# write_failure_lesson()
# ---------------------------------------------------------------------------

def test_write_failure_lesson_returns_id(store: Neo4jMemoryStore) -> None:
    lesson = FailureLesson(task_description="auth", failure_reason="null pointer")
    result = store.write_failure_lesson(lesson)
    assert result == lesson.id


def test_write_failure_lesson_executes_cypher(
    store: Neo4jMemoryStore, driver: _MockNeo4jDriver
) -> None:
    lesson = FailureLesson(task_description="auth", failure_reason="null pointer")
    store.write_failure_lesson(lesson)
    assert any("FailureLesson" in q for q in driver.queries)


def test_write_failure_lesson_passes_correct_params(
    store: Neo4jMemoryStore, driver: _MockNeo4jDriver
) -> None:
    lesson = FailureLesson(
        task_description="build auth",
        failure_reason="token expired",
        artifact_id="art-001",
        timestamp="2026-05-29T00:00:00",
    )
    store.write_failure_lesson(lesson)
    kw = driver.kwargs_log[-1]
    assert kw["id"] == lesson.id
    assert kw["task_description"] == "build auth"
    assert kw["failure_reason"] == "token expired"
    assert kw["artifact_id"] == "art-001"


def test_write_failure_lesson_unavailable_returns_none() -> None:
    store = Neo4jMemoryStore()  # no driver
    result = store.write_failure_lesson(
        FailureLesson(task_description="t", failure_reason="r")
    )
    assert result is None


def test_write_failure_lesson_exception_returns_none_and_disables() -> None:
    broken = _MockNeo4jDriver(raise_on_query=True)
    store = Neo4jMemoryStore(_driver=broken)
    result = store.write_failure_lesson(
        FailureLesson(task_description="t", failure_reason="r")
    )
    assert result is None
    assert store.is_available is False


# ---------------------------------------------------------------------------
# write_success_lesson()
# ---------------------------------------------------------------------------

def test_write_success_lesson_returns_id(store: Neo4jMemoryStore) -> None:
    lesson = SuccessLesson(task_description="auth", success_summary="all passed")
    result = store.write_success_lesson(lesson)
    assert result == lesson.id


def test_write_success_lesson_executes_cypher(
    store: Neo4jMemoryStore, driver: _MockNeo4jDriver
) -> None:
    lesson = SuccessLesson(task_description="auth", success_summary="all passed")
    store.write_success_lesson(lesson)
    assert any("SuccessLesson" in q for q in driver.queries)


def test_write_success_lesson_passes_correct_params(
    store: Neo4jMemoryStore, driver: _MockNeo4jDriver
) -> None:
    lesson = SuccessLesson(
        task_description="build auth",
        success_summary="bcrypt used, JWT validated",
        artifact_id="art-002",
        timestamp="2026-05-29T00:00:01",
    )
    store.write_success_lesson(lesson)
    kw = driver.kwargs_log[-1]
    assert kw["id"] == lesson.id
    assert kw["success_summary"] == "bcrypt used, JWT validated"
    assert kw["artifact_id"] == "art-002"


def test_write_success_lesson_unavailable_returns_none() -> None:
    store = Neo4jMemoryStore()
    result = store.write_success_lesson(
        SuccessLesson(task_description="t", success_summary="s")
    )
    assert result is None


def test_write_success_lesson_exception_returns_none_and_disables() -> None:
    broken = _MockNeo4jDriver(raise_on_query=True)
    store = Neo4jMemoryStore(_driver=broken)
    result = store.write_success_lesson(
        SuccessLesson(task_description="t", success_summary="s")
    )
    assert result is None
    assert store.is_available is False


# ---------------------------------------------------------------------------
# write_artifact_relationship()
# ---------------------------------------------------------------------------

def test_write_artifact_relationship_returns_true(store: Neo4jMemoryStore) -> None:
    rel = ArtifactRelationship(artifact_id="a1", task_id="t1", lesson_id="l1")
    assert store.write_artifact_relationship(rel) is True


def test_write_artifact_relationship_executes_cypher(
    store: Neo4jMemoryStore, driver: _MockNeo4jDriver
) -> None:
    rel = ArtifactRelationship(artifact_id="a1", task_id="t1", lesson_id="l1")
    store.write_artifact_relationship(rel)
    assert any("Artifact" in q and "Lesson" in q for q in driver.queries)


def test_write_artifact_relationship_passes_correct_params(
    store: Neo4jMemoryStore, driver: _MockNeo4jDriver
) -> None:
    rel = ArtifactRelationship(
        artifact_id="art-99", task_id="task-01", lesson_id="les-05",
        relationship_type="DERIVED_FROM",
    )
    store.write_artifact_relationship(rel)
    kw = driver.kwargs_log[-1]
    assert kw["artifact_id"] == "art-99"
    assert kw["task_id"] == "task-01"
    assert kw["lesson_id"] == "les-05"
    assert kw["relationship_type"] == "DERIVED_FROM"


def test_write_artifact_relationship_unavailable_returns_false() -> None:
    store = Neo4jMemoryStore()
    assert store.write_artifact_relationship(
        ArtifactRelationship(artifact_id="a", task_id="t", lesson_id="l")
    ) is False


def test_write_artifact_relationship_exception_returns_false_and_disables() -> None:
    broken = _MockNeo4jDriver(raise_on_query=True)
    store = Neo4jMemoryStore(_driver=broken)
    result = store.write_artifact_relationship(
        ArtifactRelationship(artifact_id="a", task_id="t", lesson_id="l")
    )
    assert result is False
    assert store.is_available is False


# ---------------------------------------------------------------------------
# close()
# ---------------------------------------------------------------------------

def test_close_marks_store_unavailable(store: Neo4jMemoryStore) -> None:
    store.close()
    assert store.is_available is False


def test_close_is_idempotent(store: Neo4jMemoryStore) -> None:
    store.close()
    store.close()  # must not raise
    assert store.is_available is False


def test_close_on_unavailable_store_does_not_raise() -> None:
    store = Neo4jMemoryStore()  # no driver, not available
    store.close()  # must not raise


def test_after_close_writes_return_safe_defaults(store: Neo4jMemoryStore) -> None:
    store.close()
    assert store.write_failure_lesson(FailureLesson(task_description="t", failure_reason="r")) is None
    assert store.write_success_lesson(SuccessLesson(task_description="t", success_summary="s")) is None
    assert store.write_artifact_relationship(ArtifactRelationship(artifact_id="a", task_id="t", lesson_id="l")) is False
    assert store.health_check() is False
