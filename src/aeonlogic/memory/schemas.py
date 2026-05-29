from dataclasses import dataclass, field
from typing import Any
import uuid


@dataclass
class Lesson:
    content: str
    source: str = "agent"
    timestamp: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class FailureLesson:
    task_description: str
    failure_reason: str
    artifact_id: str = ""
    timestamp: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class SuccessLesson:
    task_description: str
    success_summary: str
    artifact_id: str = ""
    timestamp: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class ArtifactRelationship:
    artifact_id: str
    task_id: str
    lesson_id: str
    relationship_type: str = "IMPROVED_BY"
