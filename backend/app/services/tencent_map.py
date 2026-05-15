from __future__ import annotations

from typing import Any

import httpx

from app.config import settings
from app.schemas.place import PlaceSuggestionOut

TENCENT_MAP_SUGGESTION_URL = "https://apis.map.qq.com/ws/place/v1/suggestion"


class TencentMapError(Exception):
    """Raised when Tencent Map search cannot return usable suggestions."""


class TencentMapNotConfigured(TencentMapError):
    """Raised when the Tencent Map key is missing."""


def _normalize_suggestion(item: dict[str, Any]) -> PlaceSuggestionOut | None:
    location = item.get("location")
    if not isinstance(location, dict):
        return None

    latitude = location.get("lat")
    longitude = location.get("lng")
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        return None

    title = str(item.get("title") or "").strip()
    if not title:
        return None

    return PlaceSuggestionOut(
        id=str(item.get("id") or f"{title}:{latitude}:{longitude}"),
        title=title,
        address=str(item.get("address") or "").strip(),
        category=str(item.get("category") or "").strip() or None,
        city=str(item.get("city") or "").strip() or None,
        district=str(item.get("district") or "").strip() or None,
        latitude=float(latitude),
        longitude=float(longitude),
    )


async def search_place_suggestions(
    *,
    keyword: str,
    region: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    page_size: int = 10,
) -> list[PlaceSuggestionOut]:
    key = settings.tencent_map_key.strip()
    if not key:
        raise TencentMapNotConfigured("Tencent Map search is not configured")

    params: dict[str, str | int] = {
        "key": key,
        "keyword": keyword.strip(),
        "output": "json",
        "page_size": max(1, min(page_size, 10)),
        "page_index": 1,
        "policy": 0,
    }
    if region:
        params["region"] = region.strip()
    if latitude is not None and longitude is not None:
        params["location"] = f"{latitude},{longitude}"

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(TENCENT_MAP_SUGGESTION_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as e:
        raise TencentMapError("Tencent Map search request failed") from e

    if data.get("status") != 0:
        message = str(data.get("message") or "Tencent Map search failed")
        raise TencentMapError(message)

    suggestions = []
    for item in data.get("data") or []:
        if isinstance(item, dict):
            suggestion = _normalize_suggestion(item)
            if suggestion is not None:
                suggestions.append(suggestion)
    return suggestions
