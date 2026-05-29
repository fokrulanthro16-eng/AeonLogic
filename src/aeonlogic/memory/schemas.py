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
