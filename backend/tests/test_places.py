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
    captured_params = {}

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
            captured_params.update(params)
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

    assert captured_params["key"] == "test-map-key"
    assert captured_params["keyword"] == "扬州东站"
    assert captured_params["region"] == "扬州"
    assert captured_params["location"] == "32.39,119.52"
    assert captured_params["page_size"] == 6
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
