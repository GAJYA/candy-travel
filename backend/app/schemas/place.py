from pydantic import BaseModel, ConfigDict


class PlaceSuggestionOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    address: str
    category: str | None = None
    city: str | None = None
    district: str | None = None
    latitude: float
    longitude: float
