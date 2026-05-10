from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.user import UserOut


class TripMemberRole(StrEnum):
    owner = "owner"
    editor = "editor"


class TripMemberAddIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: UUID | None = Field(default=None, validation_alias="userId")
    nickname: str | None = Field(default=None, min_length=1, max_length=64)

    @model_validator(mode="after")
    def _has_identifier(self) -> "TripMemberAddIn":
        if self.user_id is None and not self.nickname:
            raise ValueError("userId or nickname is required")
        return self


class TripMemberOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: UUID
    trip_id: UUID = Field(serialization_alias="tripId")
    role: TripMemberRole
    user: UserOut
    created_at: datetime = Field(serialization_alias="createdAt")
