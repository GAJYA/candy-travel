from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EventType(StrEnum):
    transport = "transport"
    stay = "stay"
    activity = "activity"
    reminder = "reminder"


class EventStatus(StrEnum):
    draft = "draft"
    confirmed = "confirmed"
    canceled = "canceled"


class EventSource(StrEnum):
    manual = "manual"
    ai_extracted = "ai_extracted"


class TransportMode(StrEnum):
    flight = "flight"
    train = "train"
    bus = "bus"
    car = "car"


_camel = ConfigDict(populate_by_name=True, from_attributes=True)


class TripEventCreate(BaseModel):
    model_config = _camel

    event_type: EventType = Field(validation_alias="eventType")
    title: str = Field(min_length=1, max_length=128)
    start_at: datetime = Field(validation_alias="startAt")
    end_at: datetime | None = Field(default=None, validation_alias="endAt")
    location_name: str | None = Field(
        default=None, max_length=128, validation_alias="locationName"
    )
    address: str | None = Field(default=None, max_length=256)
    note: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    status: EventStatus = EventStatus.confirmed
    sort_order: int = Field(default=0, validation_alias="sortOrder")

    @model_validator(mode="after")
    def _check_range(self) -> "TripEventCreate":
        if self.end_at and self.end_at < self.start_at:
            raise ValueError("end_at must be >= start_at")
        return self


class TripEventPatch(BaseModel):
    model_config = _camel

    title: str | None = Field(default=None, min_length=1, max_length=128)
    start_at: datetime | None = Field(default=None, validation_alias="startAt")
    end_at: datetime | None = Field(default=None, validation_alias="endAt")
    location_name: str | None = Field(
        default=None, max_length=128, validation_alias="locationName"
    )
    address: str | None = Field(default=None, max_length=256)
    note: str | None = None
    meta: dict[str, Any] | None = None
    status: EventStatus | None = None
    sort_order: int | None = Field(default=None, validation_alias="sortOrder")


class TripEventOut(BaseModel):
    model_config = _camel

    id: UUID
    trip_id: UUID = Field(serialization_alias="tripId")
    event_type: EventType = Field(serialization_alias="eventType")
    title: str
    start_at: datetime = Field(serialization_alias="startAt")
    end_at: datetime | None = Field(serialization_alias="endAt")
    location_name: str | None = Field(serialization_alias="locationName")
    address: str | None
    note: str | None
    meta: dict[str, Any]
    status: EventStatus
    source: EventSource
    sort_order: int = Field(serialization_alias="sortOrder")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
