from __future__ import annotations

from typing import Any

import httpx

from app.config import settings
from app.schemas.place import PlaceSuggestionOut

TENCENT_MAP_SUGGESTION_URL = "https://apis.map.qq.com/ws/place/v1/suggestion"
TENCENT_MAP_GEOCODER_URL = "https://apis.map.qq.com/ws/geocoder/v1/"

OVERSEAS_PLACE_HINTS: tuple[dict[str, Any], ...] = (
    {
        "aliases": ("吉隆坡", "kuala lumpur", "kl malaysia"),
        "title": "吉隆坡",
        "address": "Kuala Lumpur, Malaysia",
        "category": "城市",
        "city": "Kuala Lumpur",
        "latitude": 3.139003,
        "longitude": 101.686855,
    },
    {
        "aliases": ("马累", "马列", "malé", "male maldives", "male city maldives"),
        "title": "马累",
        "address": "Malé, Maldives",
        "category": "城市",
        "city": "Malé",
        "latitude": 4.175496,
        "longitude": 73.509347,
    },
    {
        "aliases": (
            "翡翠法鲁富士",
            "翡翠法魯富士",
            "法鲁富士",
            "法魯富士",
            "faarufushi",
            "emerald faarufushi",
        ),
        "title": "翡翠法鲁富士",
        "address": "Emerald Faarufushi Resort & Spa, Raa Atoll, Maldives",
        "category": "度假酒店",
        "city": "Raa Atoll",
        "latitude": 5.768427,
        "longitude": 72.965614,
    },
)


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


def _normalize_search_text(value: str) -> str:
    return value.strip().casefold()


def _is_overseas_hint_match(keyword: str, alias: str) -> bool:
    normalized_keyword = _normalize_search_text(keyword)
    normalized_alias = _normalize_search_text(alias)
    if not normalized_keyword or not normalized_alias:
        return False
    return normalized_keyword in normalized_alias or normalized_alias in normalized_keyword


def _matching_overseas_hints(keyword: str) -> list[PlaceSuggestionOut]:
    suggestions = []
    for hint in OVERSEAS_PLACE_HINTS:
        aliases = hint.get("aliases")
        if not isinstance(aliases, tuple):
            continue
        if not any(_is_overseas_hint_match(keyword, alias) for alias in aliases):
            continue
        title = str(hint["title"])
        latitude = float(hint["latitude"])
        longitude = float(hint["longitude"])
        suggestions.append(
            PlaceSuggestionOut(
                id=f"overseas-hint:{title}:{latitude:.6f}:{longitude:.6f}",
                title=title,
                address=str(hint["address"]),
                category=str(hint["category"]),
                city=str(hint["city"]),
                district=None,
                latitude=latitude,
                longitude=longitude,
            )
        )
    return suggestions


def _normalize_geocoder_result(
    data: dict[str, Any],
    *,
    keyword: str,
) -> PlaceSuggestionOut | None:
    result = data.get("result")
    if not isinstance(result, dict):
        return None

    location = result.get("location")
    if not isinstance(location, dict):
        return None

    latitude = location.get("lat")
    longitude = location.get("lng")
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        return None

    title = keyword.strip()
    if not title:
        return None

    address = str(result.get("address") or "").strip()
    components = result.get("address_components")
    if not isinstance(components, dict):
        components = {}

    return PlaceSuggestionOut(
        id=f"geocoder:{title}:{float(latitude):.6f}:{float(longitude):.6f}",
        title=title,
        address=address,
        category="地址解析",
        city=str(components.get("ad_level_3") or "").strip() or None,
        district=str(components.get("ad_level_4") or "").strip() or None,
        latitude=float(latitude),
        longitude=float(longitude),
    )


async def _request_tencent_json(
    client: httpx.AsyncClient,
    *,
    url: str,
    params: dict[str, str | int],
) -> dict[str, Any]:
    try:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPError, ValueError) as e:
        raise TencentMapError("Tencent Map search request failed") from e

    if not isinstance(data, dict):
        raise TencentMapError("Tencent Map search returned invalid data")

    if data.get("status") != 0:
        message = str(data.get("message") or "Tencent Map search failed")
        raise TencentMapError(message)

    return data


def _dedupe_suggestions(
    suggestions: list[PlaceSuggestionOut],
    *,
    page_size: int,
) -> list[PlaceSuggestionOut]:
    deduped: list[PlaceSuggestionOut] = []
    seen: set[tuple[str, float, float]] = set()
    for suggestion in suggestions:
        key = (
            suggestion.title,
            round(suggestion.latitude, 6),
            round(suggestion.longitude, 6),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(suggestion)
        if len(deduped) >= page_size:
            break
    return deduped


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

    normalized_keyword = keyword.strip()
    normalized_page_size = max(1, min(page_size, 10))
    params: dict[str, str | int] = {
        "key": key,
        "keyword": normalized_keyword,
        "output": "json",
        "page_size": normalized_page_size,
        "page_index": 1,
        "policy": 0,
    }
    if region:
        params["region"] = region.strip()
    if latitude is not None and longitude is not None:
        params["location"] = f"{latitude},{longitude}"

    async with httpx.AsyncClient(timeout=8) as client:
        data = await _request_tencent_json(
            client,
            url=TENCENT_MAP_SUGGESTION_URL,
            params=params,
        )

        suggestions = _matching_overseas_hints(normalized_keyword)
        for item in data.get("data") or []:
            if isinstance(item, dict):
                suggestion = _normalize_suggestion(item)
                if suggestion is not None:
                    suggestions.append(suggestion)

        if len(suggestions) < normalized_page_size:
            overseas_params: dict[str, str | int] = {
                "key": key,
                "keyword": normalized_keyword,
                "output": "json",
                "oversea": 1,
                "language": "cn",
            }
            try:
                overseas_data = await _request_tencent_json(
                    client,
                    url=TENCENT_MAP_SUGGESTION_URL,
                    params=overseas_params,
                )
            except TencentMapError:
                overseas_data = {}
            for item in overseas_data.get("data") or []:
                if isinstance(item, dict):
                    suggestion = _normalize_suggestion(item)
                    if suggestion is not None:
                        suggestions.append(suggestion)

        suggestions = _dedupe_suggestions(
            suggestions,
            page_size=normalized_page_size,
        )

        if not suggestions:
            geocoder_params: dict[str, str | int] = {
                "key": key,
                "address": normalized_keyword,
                "output": "json",
                "oversea": 1,
                "language": "cn",
            }
            try:
                geocoder_data = await _request_tencent_json(
                    client,
                    url=TENCENT_MAP_GEOCODER_URL,
                    params=geocoder_params,
                )
            except TencentMapError:
                geocoder_data = {}
            geocoded = _normalize_geocoder_result(
                geocoder_data,
                keyword=normalized_keyword,
            )
            if geocoded is not None:
                suggestions.append(geocoded)

    return suggestions[:normalized_page_size]
