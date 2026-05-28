from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from aeonlogic.utils.ids import new_ulid
from aeonlogic.utils.time import utcnow


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ModelTier(StrEnum):
    FAST = "fast"
    STRONG = "strong"


class CycleStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    EXHAUSTED = "exhausted"


class Task(BaseModel):
    id: str = Field(default_factory=new_ulid)
    description: str
    risk_level: RiskLevel = RiskLevel.MEDIUM
    created_at: datetime = Field(default_factory=utcnow)
