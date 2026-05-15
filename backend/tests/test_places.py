from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.config import settings
from app.db import SessionLocal
from app.main import app
from app.models import User
from app.schemas.place import PlaceSuggestionOut
from app.services.jwt_service import issue_token
from app.services.tencent_map import (
    TENCENT_MAP_GEOCODER_URL,
    TENCENT_MAP_SUGGESTION_URL,
    TencentMapNotConfigured,
    search_place_suggestions,
)


@pytest_asyncio.fixture
async def place_user_seed():
    async with SessionLocal() as session:
        suffix = uuid4().hex
        user = User(
            openid=f"place-search-{suffix}",
            nickname=f"Place Search {suffix[:6]}",
        )
        session.add(user)
        await session.flush()
        user_id = user.id
        token = issue_token(user_id)[0]
        await session.commit()
        data = {"user_id": user_id, "token": token}

    try:
        yield data
    finally:
        async with SessionLocal() as session:
            await session.execute(delete(User).where(User.id == data["user_id"]))
            await session.commit()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_search_places_requires_map_key(monkeypatch):
    monkeypatch.setattr(settings, "tencent_map_key", "")

    with pytest.raises(TencentMapNotConfigured):
        await search_place_suggestions(keyword="扬州东站")


@pytest.mark.asyncio
async def test_search_place_suggestions_normalizes_tencent_response(monkeypatch):
    captured_requests = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "status": 0,
                "message": "query ok",
                "data": [
                    {
                        "id": "poi-1",
                        "title": "扬州东站",
                        "address": "江苏省扬州市广陵区",
                        "category": "火车站",
                        "city": "扬州市",
                        "district": "广陵区",
                        "location": {"lat": 32.3942, "lng": 119.5257},
                    }
                ],
            }

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url, params):
            captured_requests.append({"url": url, "params": dict(params)})
            return FakeResponse()

    monkeypatch.setattr(settings, "tencent_map_key", "test-map-key")
    monkeypatch.setattr("app.services.tencent_map.httpx.AsyncClient", FakeAsyncClient)

    results = await search_place_suggestions(
        keyword="扬州东站",
        region="扬州",
        latitude=32.39,
        longitude=119.52,
        page_size=6,
    )

    first_params = captured_requests[0]["params"]
    assert captured_requests[0]["url"] == TENCENT_MAP_SUGGESTION_URL
    assert first_params["key"] == "test-map-key"
    assert first_params["keyword"] == "扬州东站"
    assert first_params["region"] == "扬州"
    assert first_params["location"] == "32.39,119.52"
    assert first_params["page_size"] == 6
    assert results == [
        PlaceSuggestionOut(
            id="poi-1",
            title="扬州东站",
            address="江苏省扬州市广陵区",
            category="火车站",
            city="扬州市",
            district="广陵区",
            latitude=32.3942,
            longitude=119.5257,
        )
    ]


@pytest.mark.asyncio
async def test_search_place_suggestions_uses_overseas_fallback(monkeypatch):
    captured_requests = []

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout
            self.responses = [
                {"status": 0, "message": "query ok", "data": []},
                {
                    "status": 0,
                    "message": "query ok",
                    "data": [
                        {
                            "id": "oversea-1",
                            "title": "White House",
                            "address": "1600 Pennsylvania Avenue NW, Washington, DC 20500, USA",
                            "category": "地标",
                            "location": {"lat": 38.897676, "lng": -77.036528},
                        }
                    ],
                },
            ]

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url, params):
            captured_requests.append({"url": url, "params": dict(params)})
            return FakeResponse(self.responses.pop(0))

    monkeypatch.setattr(settings, "tencent_map_key", "test-map-key")
    monkeypatch.setattr("app.services.tencent_map.httpx.AsyncClient", FakeAsyncClient)

    results = await search_place_suggestions(
        keyword="White House",
        region="上海",
        latitude=31.23,
        longitude=121.47,
    )

    assert len(captured_requests) == 2
    assert captured_requests[0]["params"]["region"] == "上海"
    assert captured_requests[0]["params"]["location"] == "31.23,121.47"
    assert captured_requests[1]["url"] == TENCENT_MAP_SUGGESTION_URL
    assert captured_requests[1]["params"]["oversea"] == 1
    assert captured_requests[1]["params"]["language"] == "cn"
    assert "region" not in captured_requests[1]["params"]
    assert "location" not in captured_requests[1]["params"]
    assert results == [
        PlaceSuggestionOut(
            id="oversea-1",
            title="White House",
            address="1600 Pennsylvania Avenue NW, Washington, DC 20500, USA",
            category="地标",
            city=None,
            district=None,
            latitude=38.897676,
            longitude=-77.036528,
        )
    ]


@pytest.mark.asyncio
async def test_search_place_suggestions_prioritizes_known_overseas_hint(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "status": 0,
                "message": "query ok",
                "data": [
                    {
                        "id": "domestic-1",
                        "title": "吉隆坡路",
                        "address": "广西壮族自治区崇左市宁明县",
                        "category": "道路",
                        "location": {"lat": 22.12, "lng": 107.08},
                    }
                ],
            }

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url, params):
            return FakeResponse()

    monkeypatch.setattr(settings, "tencent_map_key", "test-map-key")
    monkeypatch.setattr("app.services.tencent_map.httpx.AsyncClient", FakeAsyncClient)

    results = await search_place_suggestions(keyword="吉隆坡", page_size=2)

    assert results[0] == PlaceSuggestionOut(
        id="overseas-hint:吉隆坡:3.139003:101.686855",
        title="吉隆坡",
        address="Kuala Lumpur, Malaysia",
        category="城市",
        city="Kuala Lumpur",
        district=None,
        latitude=3.139003,
        longitude=101.686855,
    )
    assert results[1].title == "吉隆坡路"


@pytest.mark.asyncio
async def test_search_place_suggestions_uses_overseas_geocoder_fallback(monkeypatch):
    captured_requests = []

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout
            self.responses = [
                {"status": 0, "message": "query ok", "data": []},
                {"status": 0, "message": "query ok", "data": []},
                {
                    "status": 0,
                    "message": "query ok",
                    "result": {
                        "location": {"lat": 25.198189, "lng": 55.272187},
                        "address": "Dubai, United Arab Emirates",
                        "address_components": {
                            "nation": "United Arab Emirates",
                            "ad_level_3": "Dubai",
                        },
                    },
                },
            ]

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url, params):
            captured_requests.append({"url": url, "params": dict(params)})
            return FakeResponse(self.responses.pop(0))

    monkeypatch.setattr(settings, "tencent_map_key", "test-map-key")
    monkeypatch.setattr("app.services.tencent_map.httpx.AsyncClient", FakeAsyncClient)

    results = await search_place_suggestions(keyword="Atlantis Dubai")

    assert len(captured_requests) == 3
    assert captured_requests[2]["url"] == TENCENT_MAP_GEOCODER_URL
    assert captured_requests[2]["params"]["address"] == "Atlantis Dubai"
    assert captured_requests[2]["params"]["oversea"] == 1
    assert results == [
        PlaceSuggestionOut(
            id="geocoder:Atlantis Dubai:25.198189:55.272187",
            title="Atlantis Dubai",
            address="Dubai, United Arab Emirates",
            category="地址解析",
            city="Dubai",
            district=None,
            latitude=25.198189,
            longitude=55.272187,
        )
    ]


@pytest.mark.asyncio
async def test_search_places_route_returns_suggestions(client, place_user_seed, monkeypatch):
    async def fake_search_place_suggestions(**kwargs):
        assert kwargs["keyword"] == "扬州东站"
        return [
            PlaceSuggestionOut(
                id="poi-1",
                title="扬州东站",
                address="江苏省扬州市广陵区",
                category="火车站",
                city="扬州市",
                district="广陵区",
                latitude=32.3942,
                longitude=119.5257,
            )
        ]

    monkeypatch.setattr(
        "app.routes.places.search_place_suggestions",
        fake_search_place_suggestions,
    )

    response = await client.get(
        "/api/v1/places/search",
        params={"keyword": "扬州东站"},
        headers=auth_header(place_user_seed["token"]),
    )

    assert response.status_code == 200
    assert response.json()[0]["title"] == "扬州东站"
    assert response.json()[0]["latitude"] == 32.3942
