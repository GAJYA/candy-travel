from datetime import UTC, datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.db import SessionLocal
from app.main import app
from app.models import Trip, TripEvent, TripMember, User
from app.schemas.ai_import import AiTripEventCandidate
from app.services.jwt_service import issue_token


@pytest_asyncio.fixture
async def ai_trip_seed():
    async with SessionLocal() as session:
        suffix = uuid4().hex
        owner = User(openid=f"ai-owner-{suffix}", nickname=f"AI Owner {suffix[:6]}")
        stranger = User(openid=f"ai-stranger-{suffix}", nickname=f"AI Stranger {suffix[:6]}")
        session.add_all([owner, stranger])
        await session.flush()

        trip = Trip(
            user_id=owner.id,
            title="东京旅行",
            start_date=datetime(2026, 5, 20, tzinfo=UTC).date(),
            end_date=datetime(2026, 5, 23, tzinfo=UTC).date(),
            timezone="Asia/Tokyo",
        )
        session.add(trip)
        await session.flush()
        session.add(TripMember(trip_id=trip.id, user_id=owner.id, role="owner"))
        await session.commit()

        data = {
            "owner_id": owner.id,
            "stranger_id": stranger.id,
            "trip_id": trip.id,
            "owner_token": issue_token(owner.id)[0],
            "stranger_token": issue_token(stranger.id)[0],
        }

    try:
        yield data
    finally:
        async with SessionLocal() as session:
            await session.execute(
                delete(User).where(User.id.in_([data["owner_id"], data["stranger_id"]]))
            )
            await session.commit()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_extract_events_requires_auth(client, ai_trip_seed):
    response = await client.post(f"/api/v1/trips/{ai_trip_seed['trip_id']}/ai/extract-events")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_extract_events_rejects_non_image(client, ai_trip_seed):
    response = await client.post(
        f"/api/v1/trips/{ai_trip_seed['trip_id']}/ai/extract-events",
        files={"images": ("order.txt", b"not image", "text/plain")},
        headers=auth_header(ai_trip_seed["owner_token"]),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "unsupported image type"


@pytest.mark.asyncio
async def test_extract_events_rejects_inaccessible_trip(client, ai_trip_seed):
    response = await client.post(
        f"/api/v1/trips/{ai_trip_seed['trip_id']}/ai/extract-events",
        files={"images": ("order.png", b"png bytes", "image/png")},
        headers=auth_header(ai_trip_seed["stranger_token"]),
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_extract_events_uses_service(monkeypatch, client, ai_trip_seed):
    async def fake_extract_trip_events(*, trip, images, client_timezone=None):
        assert trip.id == ai_trip_seed["trip_id"]
        assert images == [(b"png bytes", "image/png")]
        assert client_timezone is None
        return (
            [
                AiTripEventCandidate.model_validate(
                    {
                        "clientId": "tmp_1",
                        "eventType": "transport",
                        "title": "航班 MU123 上海虹桥 -> 东京羽田",
                        "startAt": "2026-05-20T09:30:00+08:00",
                        "endAt": "2026-05-20T12:45:00+09:00",
                        "locationName": "上海虹桥国际机场",
                        "meta": {"icon": "plane", "allDay": False, "orderType": "flight"},
                        "confidence": "high",
                        "warnings": [],
                    }
                )
            ],
            [],
            "gpt-5.5",
        )

    monkeypatch.setattr("app.routes.ai_import.extract_trip_events", fake_extract_trip_events)

    response = await client.post(
        f"/api/v1/trips/{ai_trip_seed['trip_id']}/ai/extract-events",
        files={"images": ("order.png", b"png bytes", "image/png")},
        headers=auth_header(ai_trip_seed["owner_token"]),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "gpt-5.5"
    assert body["events"][0]["title"] == "航班 MU123 上海虹桥 -> 东京羽田"


@pytest.mark.asyncio
async def test_import_events_creates_ai_extracted_events(client, ai_trip_seed):
    response = await client.post(
        f"/api/v1/trips/{ai_trip_seed['trip_id']}/ai/import-events",
        json={
            "events": [
                {
                    "clientId": "tmp_1",
                    "eventType": "stay",
                    "title": "入住新宿酒店",
                    "startAt": "2026-05-20T00:00:00+09:00",
                    "endAt": "2026-05-23T00:00:00+09:00",
                    "locationName": "新宿酒店",
                    "address": "东京都新宿区",
                    "note": "高级双床房",
                    "meta": {"icon": "hotel", "allDay": True, "orderType": "hotel"},
                    "confidence": "high",
                    "warnings": [],
                    "sortOrder": 0,
                }
            ]
        },
        headers=auth_header(ai_trip_seed["owner_token"]),
    )

    assert response.status_code == 201
    body = response.json()
    assert body[0]["source"] == "ai_extracted"
    assert body[0]["eventType"] == "stay"

    async with SessionLocal() as session:
        event = await session.scalar(select(TripEvent).where(TripEvent.id == body[0]["id"]))
        assert event is not None
        assert event.source == "ai_extracted"
