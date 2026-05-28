from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from aeonlogic.utils.ids import new_ulid
from aeonlogic.utils.time import utcnow


class ExecutionStatus(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"


class Result(BaseModel):
    id: str = Field(default_factory=new_ulid)
    task_id: str
    artifact_id: str
    status: ExecutionStatus
    summary: str
    stdout: str = ""
    stderr: str = ""
    duration_ms: int = 0
    created_at: datetime = Field(default_factory=utcnow)
