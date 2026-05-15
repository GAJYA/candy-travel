from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class InspirationType(StrEnum):
    short = "short"
    long = "long"


class InspirationStatus(StrEnum):
    idea = "idea"
    planned = "planned"


_camel_config = ConfigDict(populate_by_name=True, from_attributes=True)


class InspirationCreate(BaseModel):
    model_config = _camel_config

    destination: str = Field(min_length=1, max_length=64)
    type: InspirationType
    note: str | None = Field(default=None, max_length=500)
    source_url: str | None = Field(
        default=None, max_length=1024, validation_alias="sourceUrl"
    )
    plan_detail: str | None = Field(
        default=None, max_length=4000, validation_alias="planDetail"
    )

    @field_validator("destination", mode="before")
    @classmethod
    def _strip_required(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value

    @field_validator("note", "source_url", "plan_detail")
    @classmethod
    def _strip_note(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip() or None


class InspirationPatch(BaseModel):
    model_config = _camel_config

    destination: str | None = Field(default=None, min_length=1, max_length=64)
    type: InspirationType | None = None
    note: str | None = Field(default=None, max_length=500)
    source_url: str | None = Field(
        default=None, max_length=1024, validation_alias="sourceUrl"
    )
    plan_detail: str | None = Field(
        default=None, max_length=4000, validation_alias="planDetail"
    )
    status: InspirationStatus | None = None

    @field_validator("destination", mode="before")
    @classmethod
    def _strip_optional_required(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip() if isinstance(value, str) else value

    @field_validator("note", "source_url", "plan_detail")
    @classmethod
    def _strip_note(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip() or None


class InspirationFromShareIn(BaseModel):
    model_config = _camel_config

    shared_text: str = Field(min_length=1, max_length=4096, validation_alias="sharedText")
    type: InspirationType = InspirationType.short

    @field_validator("shared_text", mode="before")
    @classmethod
    def _strip_shared_text(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value


class InspirationOut(BaseModel):
    model_config = _camel_config

    id: UUID
    destination: str
    type: InspirationType
    source_url: str | None = Field(serialization_alias="sourceUrl")
    note: str | None
    plan_detail: str | None = Field(serialization_alias="planDetail")
    status: InspirationStatus
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
