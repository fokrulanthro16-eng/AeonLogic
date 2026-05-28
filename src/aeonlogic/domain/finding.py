from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from aeonlogic.utils.ids import new_ulid
from aeonlogic.utils.time import utcnow


class FindingSeverity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Verdict(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"


class Finding(BaseModel):
    id: str = Field(default_factory=new_ulid)
    artifact_id: str
    severity: FindingSeverity
    category: str
    title: str
    description: str
    evidence: str = ""
    recommendation: str = ""
    created_at: datetime = Field(default_factory=utcnow)
