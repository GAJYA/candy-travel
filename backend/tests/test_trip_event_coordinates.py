from datetime import UTC, datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.db import SessionLocal
from app.main import app
from app.models import Trip, TripEvent, TripMember, User
from app.services.jwt_service import issue_token


@pytest_asyncio.fixture
async def coordinate_trip_seed():
    async with SessionLocal() as session:
        suffix = uuid4().hex
        owner = User(
            openid=f"coordinate-owner-{suffix}",
            nickname=f"Coordinate Owner {suffix[:6]}",
        )
        session.add(owner)
        await session.flush()

        trip = Trip(
            user_id=owner.id,
            title="杭州路线",
            start_date=datetime(2026, 6, 1, tzinfo=UTC).date(),
            end_date=datetime(2026, 6, 3, tzinfo=UTC).date(),
            timezone="Asia/Shanghai",
        )
        session.add(trip)
        await session.flush()
        session.add(TripMember(trip_id=trip.id, user_id=owner.id, role="owner"))
        await session.commit()

        data = {
            "owner_id": owner.id,
            "trip_id": trip.id,
            "owner_token": issue_token(owner.id)[0],
        }

    try:
        yield data
    finally:
        async with SessionLocal() as session:
            await session.execute(delete(User).where(User.id == data["owner_id"]))
            await session.commit()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_and_list_event_coordinates(client, coordinate_trip_seed):
    headers = auth_header(coordinate_trip_seed["owner_token"])

    created = await client.post(
        f"/api/v1/trips/{coordinate_trip_seed['trip_id']}/events",
        json={
            "eventType": "activity",
            "title": "西湖边散步",
            "startAt": "2026-06-01T02:00:00Z",
            "locationName": "西湖",
            "address": "浙江省杭州市西湖区",
            "latitude": 30.24258,
            "longitude": 120.15062,
            "meta": {"icon": "park", "allDay": False},
        },
        headers=headers,
    )

    assert created.status_code == 201
    created_body = created.json()
    created_event_id = created_body["id"]

    listed = await client.get(
        f"/api/v1/trips/{coordinate_trip_seed['trip_id']}/events",
        headers=headers,
    )

    assert listed.status_code == 200
    listed_body = listed.json()
    assert [event["id"] for event in listed_body] == [created_event_id]
    listed_event = listed_body[0]

    assert created_body["latitude"] == 30.24258
    assert created_body["longitude"] == 120.15062
    assert listed_event["latitude"] == 30.24258
    assert listed_event["longitude"] == 120.15062


@pytest.mark.asyncio
async def test_patch_location_text_preserves_existing_coordinates(client, coordinate_trip_seed):
    headers = auth_header(coordinate_trip_seed["owner_token"])
    created = await client.post(
        f"/api/v1/trips/{coordinate_trip_seed['trip_id']}/events",
        json={
            "eventType": "activity",
            "title": "酒店办理入住",
            "startAt": "2026-06-01T07:00:00Z",
            "locationName": "全季酒店杭州西湖店",
            "address": "杭州市上城区",
            "latitude": 30.25308,
            "longitude": 120.16572,
            "meta": {"icon": "hotel", "allDay": False},
        },
        headers=headers,
    )
    assert created.status_code == 201
    event_id = created.json()["id"]

    updated = await client.patch(
        f"/api/v1/events/{event_id}",
        json={"locationName": "酒店", "address": "离地铁站近"},
        headers=headers,
    )

    assert updated.status_code == 200
    body = updated.json()
    assert body["locationName"] == "酒店"
    assert body["address"] == "离地铁站近"
    assert body["latitude"] == 30.25308
    assert body["longitude"] == 120.16572


@pytest.mark.asyncio
async def test_patch_coordinates_updates_coordinates(client, coordinate_trip_seed):
    headers = auth_header(coordinate_trip_seed["owner_token"])
    created = await client.post(
        f"/api/v1/trips/{coordinate_trip_seed['trip_id']}/events",
        json={
            "eventType": "activity",
            "title": "咖啡",
            "startAt": "2026-06-01T08:00:00Z",
            "locationName": "咖啡店 A",
            "latitude": 30.25,
            "longitude": 120.16,
            "meta": {"icon": "coffee", "allDay": False},
        },
        headers=headers,
    )
    assert created.status_code == 201

    updated = await client.patch(
        f"/api/v1/events/{created.json()['id']}",
        json={
            "locationName": "咖啡店 B",
            "latitude": 30.27415,
            "longitude": 120.15515,
        },
        headers=headers,
    )

    assert updated.status_code == 200
    body = updated.json()
    assert body["locationName"] == "咖啡店 B"
    assert body["latitude"] == 30.27415
    assert body["longitude"] == 120.15515


@pytest.mark.asyncio
async def test_patch_coordinates_can_clear_coordinates(client, coordinate_trip_seed):
    headers = auth_header(coordinate_trip_seed["owner_token"])
    created = await client.post(
        f"/api/v1/trips/{coordinate_trip_seed['trip_id']}/events",
        json={
            "eventType": "activity",
            "title": "上海出发",
            "startAt": "2026-06-01T00:00:00Z",
            "locationName": "上海虹桥站",
            "address": "上海市闵行区",
            "latitude": 31.19482,
            "longitude": 121.32695,
            "meta": {"icon": "train", "allDay": False},
        },
        headers=headers,
    )
    assert created.status_code == 201

    updated = await client.patch(
        f"/api/v1/events/{created.json()['id']}",
        json={
            "address": None,
            "latitude": None,
            "longitude": None,
        },
        headers=headers,
    )

    assert updated.status_code == 200
    body = updated.json()
    assert body["locationName"] == "上海虹桥站"
    assert body["address"] is None
    assert body["latitude"] is None
    assert body["longitude"] is None


@pytest.mark.asyncio
async def test_rejects_incomplete_or_out_of_range_coordinates(client, coordinate_trip_seed):
    headers = auth_header(coordinate_trip_seed["owner_token"])

    invalid_payloads = [
        {
            "eventType": "activity",
            "title": "只有纬度",
            "startAt": "2026-06-01T08:30:00Z",
            "latitude": 30.27,
            "meta": {"icon": "pin", "allDay": False},
        },
        {
            "eventType": "activity",
            "title": "只有经度",
            "startAt": "2026-06-01T08:45:00Z",
            "longitude": 120.15,
            "meta": {"icon": "pin", "allDay": False},
        },
        {
            "eventType": "activity",
            "title": "非法纬度",
            "startAt": "2026-06-01T09:00:00Z",
            "latitude": 91,
            "longitude": 120.15,
            "meta": {"icon": "pin", "allDay": False},
        },
        {
            "eventType": "activity",
            "title": "非法经度",
            "startAt": "2026-06-01T09:15:00Z",
            "latitude": 30.27,
            "longitude": 181,
            "meta": {"icon": "pin", "allDay": False},
        },
    ]

    for payload in invalid_payloads:
        response = await client.post(
            f"/api/v1/trips/{coordinate_trip_seed['trip_id']}/events",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_ai_import_events_can_persist_coordinates(client, coordinate_trip_seed):
    headers = auth_header(coordinate_trip_seed["owner_token"])

    response = await client.post(
        f"/api/v1/trips/{coordinate_trip_seed['trip_id']}/ai/import-events",
        json={
            "events": [
                {
                    "clientId": "tmp_1",
                    "eventType": "activity",
                    "title": "灵隐寺",
                    "startAt": "2026-06-02T02:00:00Z",
                    "locationName": "灵隐寺",
                    "address": "浙江省杭州市西湖区法云弄1号",
                    "latitude": 30.24006,
                    "longitude": 120.10235,
                    "note": None,
                    "meta": {"icon": "museum", "allDay": False},
                    "confidence": "high",
                    "warnings": [],
                    "sortOrder": 0,
                }
            ]
        },
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body[0]["latitude"] == 30.24006
    assert body[0]["longitude"] == 120.10235

    async with SessionLocal() as session:
        event = await session.scalar(select(TripEvent).where(TripEvent.id == body[0]["id"]))
        assert event is not None
        assert event.latitude == 30.24006
        assert event.longitude == 120.10235
