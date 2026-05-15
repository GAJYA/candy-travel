from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.trip_event import EventType

Confidence = Literal["high", "medium", "low"]

_camel = ConfigDict(populate_by_name=True)


class AiTripEventCandidate(BaseModel):
    model_config = _camel

    client_id: str = Field(validation_alias="clientId", serialization_alias="clientId")
    event_type: EventType = Field(validation_alias="eventType", serialization_alias="eventType")
    title: str = Field(min_length=1, max_length=128)
    start_at: datetime | None = Field(
        default=None,
        validation_alias="startAt",
        serialization_alias="startAt",
    )
    end_at: datetime | None = Field(
        default=None,
        validation_alias="endAt",
        serialization_alias="endAt",
    )
    location_name: str | None = Field(
        default=None,
        max_length=128,
        validation_alias="locationName",
        serialization_alias="locationName",
    )
    address: str | None = Field(default=None, max_length=256)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    note: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    confidence: Confidence = "medium"
    warnings: list[str] = Field(default_factory=list)
    sort_order: int = Field(
        default=0,
        validation_alias="sortOrder",
        serialization_alias="sortOrder",
    )

    @model_validator(mode="after")
    def _check_values(self) -> "AiTripEventCandidate":
        if self.end_at is not None and self.start_at is not None and self.end_at < self.start_at:
            raise ValueError("end_at must be >= start_at")
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be provided together")
        return self


class AiExtractEventsResponse(BaseModel):
    model_config = _camel

    trip_id: UUID = Field(serialization_alias="tripId")
    model: str
    events: list[AiTripEventCandidate]
    warnings: list[str] = Field(default_factory=list)


class AiImportEventsIn(BaseModel):
    model_config = _camel

    events: list[AiTripEventCandidate] = Field(min_length=1, max_length=30)
