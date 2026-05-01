from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nickname: str | None = None
    avatar_url: str | None = Field(default=None, serialization_alias="avatarUrl")
    locale: str
    timezone: str
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class UserPatchIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    nickname: str | None = Field(default=None, max_length=64)
    avatar_url: str | None = Field(
        default=None, max_length=512, validation_alias="avatarUrl"
    )
    locale: str | None = Field(default=None, max_length=16)
    timezone: str | None = Field(default=None, max_length=32)
