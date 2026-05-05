from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChecklistCategory(StrEnum):
    document = "document"
    electronics = "electronics"
    clothing = "clothing"
    medicine = "medicine"
    food = "food"
    home = "home"
    pet = "pet"
    task = "task"
    other = "other"


class ChecklistSource(StrEnum):
    template = "template"
    manual = "manual"
    ai_generated = "ai_generated"


_camel = ConfigDict(populate_by_name=True, from_attributes=True)


class ChecklistTemplateOut(BaseModel):
    model_config = _camel

    id: UUID
    label: str
    category: ChecklistCategory
    sort_order: int = Field(serialization_alias="sortOrder")
    is_default: bool = Field(serialization_alias="isDefault")


class ChecklistItemCreate(BaseModel):
    model_config = _camel

    label: str = Field(min_length=1, max_length=64)
    category: ChecklistCategory = ChecklistCategory.other
    sort_order: int = Field(default=0, validation_alias="sortOrder")
    template_id: UUID | None = Field(default=None, validation_alias="templateId")
    checked: bool = False


class ChecklistItemPatch(BaseModel):
    model_config = _camel

    label: str | None = Field(default=None, min_length=1, max_length=64)
    category: ChecklistCategory | None = None
    sort_order: int | None = Field(default=None, validation_alias="sortOrder")
    checked: bool | None = None


class ChecklistItemOut(BaseModel):
    model_config = _camel

    id: UUID
    trip_id: UUID = Field(serialization_alias="tripId")
    label: str
    checked: bool
    category: ChecklistCategory
    source: ChecklistSource
    template_id: UUID | None = Field(serialization_alias="templateId")
    sort_order: int = Field(serialization_alias="sortOrder")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
