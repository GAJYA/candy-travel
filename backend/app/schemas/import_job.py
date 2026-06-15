from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.inspiration import InspirationShareDraftOut

_camel_config = ConfigDict(populate_by_name=True, from_attributes=True)


class ImportJobStatus(StrEnum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    expired = "expired"


class InspirationImportJobOut(BaseModel):
    model_config = _camel_config

    id: UUID
    status: ImportJobStatus
    result: InspirationShareDraftOut | None = None
    error_message: str | None = Field(default=None, serialization_alias="errorMessage")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
    expires_at: datetime = Field(serialization_alias="expiresAt")
    started_at: datetime | None = Field(default=None, serialization_alias="startedAt")
    finished_at: datetime | None = Field(default=None, serialization_alias="finishedAt")
