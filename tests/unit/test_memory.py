"""Unit tests: in-process memory store mechanics."""
from __future__ import annotations

from aeonlogic.agents.memory_synthesizer import _store, _write, get_all_lessons


def test_write_creates_lesson_with_ulid() -> None:
    lesson = _write("test-type", "test content")
    assert lesson.id
    assert len(lesson.id) == 26  # ULID is always 26 chars


def test_write_sets_type_and_content() -> None:
    lesson = _write("failure-lesson", "something went wrong")
    assert lesson.lesson_type == "failure-lesson"
    assert lesson.content == "something went wrong"


def test_write_sets_tags() -> None:
    lesson = _write("success-lesson", "it worked", tags="security,auth")
    assert lesson.tags == "security,auth"


def test_write_appends_to_store() -> None:
    assert len(_store) == 0         # autouse fixture cleared it
    _write("a", "first lesson")
    _write("b", "second lesson")
    assert len(_store) == 2


def test_get_all_lessons_returns_shallow_copy() -> None:
    _write("x", "y")
    copy = get_all_lessons()
    copy.clear()                    # mutate the copy
    assert len(_store) == 1         # original unaffected


def test_lesson_ids_are_unique() -> None:
    _write("type", "content alpha")
    _write("type", "content beta")
    ids = [l.id for l in _store]
    assert len(set(ids)) == len(ids)


def test_store_is_empty_at_start_of_each_test() -> None:
    # Verifies the autouse fixture in conftest.py works correctly
    assert len(_store) == 0
