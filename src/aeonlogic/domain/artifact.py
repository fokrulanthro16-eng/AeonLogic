from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from aeonlogic.utils.hashing import sha256_hex
from aeonlogic.utils.ids import new_ulid
from aeonlogic.utils.time import utcnow


class ArtifactType(StrEnum):
    CODE = "code"
    PLAN = "plan"
    ANALYSIS = "analysis"
    DATA = "data"


class Artifact(BaseModel):
    id: str = Field(default_factory=new_ulid)
    task_id: str
    artifact_type: ArtifactType = ArtifactType.ANALYSIS
    content: str
    content_hash: str = ""
    created_at: datetime = Field(default_factory=utcnow)

    @model_validator(mode="after")
    def _set_content_hash(self) -> Artifact:
        if not self.content_hash:
            self.content_hash = sha256_hex(self.content)
        return self
