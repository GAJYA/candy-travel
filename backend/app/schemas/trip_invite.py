from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.trip_member import TripMemberOut


class TripInviteStatus(StrEnum):
    active = "active"
    expired = "expired"
    accepted = "accepted"


class TripInviteCreateOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    trip_id: UUID = Field(serialization_alias="tripId")
    code: str
    expires_at: datetime = Field(serialization_alias="expiresAt")


class TripInvitePreviewOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    trip_id: UUID = Field(serialization_alias="tripId")
    trip_title: str = Field(serialization_alias="tripTitle")
    inviter_nickname: str | None = Field(serialization_alias="inviterNickname")
    status: TripInviteStatus
    expires_at: datetime = Field(serialization_alias="expiresAt")


class TripInviteAcceptOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    trip_id: UUID = Field(serialization_alias="tripId")
    member: TripMemberOut


class TripInviteAcceptIn(BaseModel):
    code: str = Field(min_length=4, max_length=16)
