from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TripStatus(StrEnum):
    draft = "draft"
    planning = "planning"
    confirmed = "confirmed"
    completed = "completed"
    canceled = "canceled"
    archived = "archived"


class TripCreatedVia(StrEnum):
    manual = "manual"
    ai_import = "ai_import"


_camel_config = ConfigDict(populate_by_name=True, from_attributes=True)


class TripCreate(BaseModel):
    model_config = _camel_config

    title: str = Field(min_length=1, max_length=128)
    destination_city: str | None = Field(
        default=None, max_length=64, validation_alias="destinationCity"
    )
    status: TripStatus = TripStatus.draft
    start_date: date | None = Field(default=None, validation_alias="startDate")
    end_date: date | None = Field(default=None, validation_alias="endDate")
    cover_image_url: str | None = Field(
        default=None, max_length=512, validation_alias="coverImageUrl"
    )
    note: str | None = None
    timezone: str = Field(default="Asia/Shanghai", max_length=32)

    @model_validator(mode="after")
    def _date_range(self) -> "TripCreate":
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must be <= end_date")
        return self


class TripPatch(BaseModel):
    model_config = _camel_config

    title: str | None = Field(default=None, min_length=1, max_length=128)
    destination_city: str | None = Field(
        default=None, max_length=64, validation_alias="destinationCity"
    )
    status: TripStatus | None = None
    start_date: date | None = Field(default=None, validation_alias="startDate")
    end_date: date | None = Field(default=None, validation_alias="endDate")
    cover_image_url: str | None = Field(
        default=None, max_length=512, validation_alias="coverImageUrl"
    )
    note: str | None = None
    timezone: str | None = Field(default=None, max_length=32)

    @field_validator("title")
    @classmethod
    def _title_strip(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class TripOut(BaseModel):
    model_config = _camel_config

    id: UUID
    title: str
    destination_city: str | None = Field(serialization_alias="destinationCity")
    status: TripStatus
    start_date: date | None = Field(serialization_alias="startDate")
    end_date: date | None = Field(serialization_alias="endDate")
    cover_image_url: str | None = Field(serialization_alias="coverImageUrl")
    note: str | None
    timezone: str
    created_via: TripCreatedVia = Field(serialization_alias="createdVia")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
