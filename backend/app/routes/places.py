from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.deps import CurrentUser
from app.schemas.place import PlaceSuggestionOut
from app.services.tencent_map import (
    TencentMapError,
    TencentMapNotConfigured,
    search_place_suggestions,
)

router = APIRouter(prefix="/places", tags=["places"])


@router.get("/search", response_model=list[PlaceSuggestionOut], response_model_by_alias=True)
async def search_places(
    user: CurrentUser,
    keyword: Annotated[str, Query(min_length=1, max_length=80)],
    region: Annotated[str | None, Query(max_length=32)] = None,
    latitude: Annotated[float | None, Query(ge=-90, le=90)] = None,
    longitude: Annotated[float | None, Query(ge=-180, le=180)] = None,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=10)] = 10,
) -> list[PlaceSuggestionOut]:
    del user
    if (latitude is None) != (longitude is None):
        raise HTTPException(
            status_code=400,
            detail="latitude and longitude must be provided together",
        )

    try:
        return await search_place_suggestions(
            keyword=keyword,
            region=region,
            latitude=latitude,
            longitude=longitude,
            page_size=page_size,
        )
    except TencentMapNotConfigured as e:
        raise HTTPException(status_code=503, detail="map search is not configured") from e
    except TencentMapError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
