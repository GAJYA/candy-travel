from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.trip import TripOut, TripStatus
from app.schemas.trip_event import TransportMode

_camel = ConfigDict(populate_by_name=True, from_attributes=True)


class TripTransportSummary(BaseModel):
    model_config = _camel

    event_id: UUID = Field(serialization_alias="eventId")
    mode: TransportMode | None = None
    depart_at: datetime | None = Field(serialization_alias="departAt")
    arrive_at: datetime | None = Field(serialization_alias="arriveAt")
    from_city: str | None = Field(default=None, serialization_alias="fromCity")
    to_city: str | None = Field(default=None, serialization_alias="toCity")
    flight_no: str | None = Field(default=None, serialization_alias="flightNo")
    train_no: str | None = Field(default=None, serialization_alias="trainNo")
    seat: str | None = None
    ref_code: str | None = Field(default=None, serialization_alias="refCode")


class TripStaySummary(BaseModel):
    model_config = _camel

    event_id: UUID = Field(serialization_alias="eventId")
    hotel_name: str | None = Field(serialization_alias="hotelName")
    checkin_at: datetime | None = Field(serialization_alias="checkinAt")
    checkout_at: datetime | None = Field(serialization_alias="checkoutAt")
    address: str | None = None
    room_type: str | None = Field(default=None, serialization_alias="roomType")
    ref_code: str | None = Field(default=None, serialization_alias="refCode")
    guests: int | None = None


class TripSummaryOut(BaseModel):
    model_config = _camel

    transport: TripTransportSummary | None = None
    stay: TripStaySummary | None = None


class TripDetailOut(TripOut):
    summary: TripSummaryOut


# ---- PATCH /trips/:id/summary 请求体 ----


class TripTransportPatch(BaseModel):
    """transport 段输入，全字段可选；进 meta 与 start/end_at"""

    model_config = _camel

    mode: TransportMode | None = None
    depart_at: datetime | None = Field(default=None, validation_alias="departAt")
    arrive_at: datetime | None = Field(default=None, validation_alias="arriveAt")
    from_city: str | None = Field(default=None, validation_alias="fromCity", max_length=64)
    to_city: str | None = Field(default=None, validation_alias="toCity", max_length=64)
    flight_no: str | None = Field(default=None, validation_alias="flightNo", max_length=32)
    train_no: str | None = Field(default=None, validation_alias="trainNo", max_length=32)
    seat: str | None = Field(default=None, max_length=32)
    ref_code: str | None = Field(default=None, validation_alias="refCode", max_length=64)


class TripStayPatch(BaseModel):
    model_config = _camel

    hotel_name: str | None = Field(default=None, validation_alias="hotelName", max_length=128)
    checkin_at: datetime | None = Field(default=None, validation_alias="checkinAt")
    checkout_at: datetime | None = Field(default=None, validation_alias="checkoutAt")
    address: str | None = Field(default=None, max_length=256)
    room_type: str | None = Field(default=None, validation_alias="roomType", max_length=64)
    ref_code: str | None = Field(default=None, validation_alias="refCode", max_length=64)
    guests: int | None = None


class TripSummaryPatchIn(BaseModel):
    """合并 trip 顶级字段 patch + transport / stay 段 upsert/删除"""

    model_config = _camel

    # trip 顶级字段（与 TripPatch 子集一致）
    title: str | None = Field(default=None, min_length=1, max_length=128)
    destination_city: str | None = Field(
        default=None, validation_alias="destinationCity", max_length=64
    )
    note: str | None = None
    status: TripStatus | None = None
    start_date: date | None = Field(default=None, validation_alias="startDate")
    end_date: date | None = Field(default=None, validation_alias="endDate")
    timezone: str | None = Field(default=None, max_length=32)

    # 摘要段：unset 不动，None 软删，对象 upsert
    transport: TripTransportPatch | None = None
    stay: TripStayPatch | None = None
