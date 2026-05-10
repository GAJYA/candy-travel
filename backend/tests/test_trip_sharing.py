from datetime import UTC, datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.db import SessionLocal
from app.main import app
from app.models import ChecklistItem, Trip, TripMember, User
from app.services.jwt_service import issue_token


@pytest_asyncio.fixture
async def shared_trip_seed():
    async with SessionLocal() as session:
        suffix = uuid4().hex
        owner = User(openid=f"owner-{suffix}", nickname=f"Owner {suffix[:6]}")
        editor = User(openid=f"editor-{suffix}", nickname=f"Editor {suffix[:6]}")
        recipient = User(openid=f"recipient-{suffix}", nickname=f"Recipient {suffix[:6]}")
        session.add_all([owner, editor, recipient])
        await session.flush()

        trip = Trip(
            user_id=owner.id,
            title="Kyoto spring",
            start_date=datetime(2026, 4, 1, tzinfo=UTC).date(),
            end_date=datetime(2026, 4, 5, tzinfo=UTC).date(),
            timezone="Asia/Shanghai",
        )
        session.add(trip)
        await session.flush()
        session.add(TripMember(trip_id=trip.id, user_id=owner.id, role="owner"))

        item = ChecklistItem(
            user_id=owner.id,
            trip_id=trip.id,
            label="护照",
            category="document",
            source="manual",
            sort_order=10,
        )
        session.add(item)
        await session.commit()

        data = {
            "owner_id": owner.id,
            "editor_id": editor.id,
            "editor_nickname": editor.nickname,
            "recipient_id": recipient.id,
            "trip_id": trip.id,
            "item_id": item.id,
            "owner_token": issue_token(owner.id)[0],
            "editor_token": issue_token(editor.id)[0],
            "recipient_token": issue_token(recipient.id)[0],
        }

    try:
        yield data
    finally:
        async with SessionLocal() as session:
            await session.execute(
                delete(User).where(
                    User.id.in_(
                        [
                            data["owner_id"],
                            data["editor_id"],
                            data["recipient_id"],
                        ]
                    )
                )
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
async def test_invited_user_can_view_and_edit_shared_trip(client, shared_trip_seed):
    owner_headers = auth_header(shared_trip_seed["owner_token"])
    editor_headers = auth_header(shared_trip_seed["editor_token"])
    trip_id = shared_trip_seed["trip_id"]

    invite = await client.post(
        f"/api/v1/trips/{trip_id}/members",
        json={"userId": str(shared_trip_seed["editor_id"])},
        headers=owner_headers,
    )
    assert invite.status_code == 201
    assert invite.json()["role"] == "editor"

    members = await client.get(f"/api/v1/trips/{trip_id}/members", headers=owner_headers)
    assert members.status_code == 200
    assert [member["role"] for member in members.json()] == ["owner", "editor"]

    editor_view = await client.get(f"/api/v1/trips/{trip_id}", headers=editor_headers)
    assert editor_view.status_code == 200
    assert editor_view.json()["title"] == "Kyoto spring"

    editor_list = await client.get("/api/v1/trips", headers=editor_headers)
    assert editor_list.status_code == 200
    assert [trip["id"] for trip in editor_list.json()] == [str(trip_id)]

    updated = await client.patch(
        f"/api/v1/trips/{trip_id}/summary",
        json={"title": "Kyoto shared spring"},
        headers=editor_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Kyoto shared spring"

    owner_view = await client.get(f"/api/v1/trips/{trip_id}", headers=owner_headers)
    assert owner_view.status_code == 200
    assert owner_view.json()["title"] == "Kyoto shared spring"


@pytest.mark.asyncio
async def test_shared_editor_can_edit_events_and_checklist(client, shared_trip_seed):
    owner_headers = auth_header(shared_trip_seed["owner_token"])
    editor_headers = auth_header(shared_trip_seed["editor_token"])
    trip_id = shared_trip_seed["trip_id"]

    invite = await client.post(
        f"/api/v1/trips/{trip_id}/members",
        json={"nickname": shared_trip_seed["editor_nickname"]},
        headers=owner_headers,
    )
    assert invite.status_code == 201

    created_event = await client.post(
        f"/api/v1/trips/{trip_id}/events",
        json={
            "eventType": "activity",
            "title": "清水寺",
            "startAt": "2026-04-02T02:00:00Z",
            "meta": {"icon": "pin", "allDay": False},
            "status": "confirmed",
        },
        headers=editor_headers,
    )
    assert created_event.status_code == 201

    owner_events = await client.get(f"/api/v1/trips/{trip_id}/events", headers=owner_headers)
    assert owner_events.status_code == 200
    assert [event["id"] for event in owner_events.json()] == [created_event.json()["id"]]

    checked = await client.patch(
        f"/api/v1/checklist-items/{shared_trip_seed['item_id']}",
        json={"checked": True},
        headers=editor_headers,
    )
    assert checked.status_code == 200
    assert checked.json()["checked"] is True

    owner_items = await client.get(
        f"/api/v1/trips/{trip_id}/checklist-items",
        headers=owner_headers,
    )
    assert owner_items.status_code == 200
    assert owner_items.json()[0]["checked"] is True


@pytest.mark.asyncio
async def test_trip_can_be_marked_canceled(client, shared_trip_seed):
    owner_headers = auth_header(shared_trip_seed["owner_token"])
    trip_id = shared_trip_seed["trip_id"]

    updated = await client.patch(
        f"/api/v1/trips/{trip_id}/summary",
        json={"status": "canceled"},
        headers=owner_headers,
    )

    assert updated.status_code == 200
    assert updated.json()["status"] == "canceled"


@pytest.mark.asyncio
async def test_shared_editor_cannot_delete_whole_trip(client, shared_trip_seed):
    owner_headers = auth_header(shared_trip_seed["owner_token"])
    editor_headers = auth_header(shared_trip_seed["editor_token"])
    trip_id = shared_trip_seed["trip_id"]

    invite = await client.post(
        f"/api/v1/trips/{trip_id}/members",
        json={"userId": str(shared_trip_seed["editor_id"])},
        headers=owner_headers,
    )
    assert invite.status_code == 201

    deleted = await client.delete(f"/api/v1/trips/{trip_id}", headers=editor_headers)
    assert deleted.status_code == 403

    owner_view = await client.get(f"/api/v1/trips/{trip_id}", headers=owner_headers)
    assert owner_view.status_code == 200


@pytest.mark.asyncio
async def test_invite_code_adds_first_logged_in_recipient_to_trip(client, shared_trip_seed):
    owner_headers = auth_header(shared_trip_seed["owner_token"])
    recipient_headers = auth_header(shared_trip_seed["recipient_token"])
    editor_headers = auth_header(shared_trip_seed["editor_token"])
    trip_id = shared_trip_seed["trip_id"]

    created = await client.post(f"/api/v1/trips/{trip_id}/invite", headers=owner_headers)
    assert created.status_code == 201
    invite = created.json()
    assert invite["tripId"] == str(trip_id)
    assert len(invite["code"]) == 6
    assert invite["code"].isalnum()

    preview = await client.get(f"/api/v1/trip-invites/{invite['code'].lower()}")
    assert preview.status_code == 200
    assert preview.json()["tripTitle"] == "Kyoto spring"
    assert preview.json()["status"] == "active"

    accepted = await client.post(
        "/api/v1/trip-invites/accept",
        json={"code": invite["code"].lower()},
        headers=recipient_headers,
    )
    assert accepted.status_code == 200
    assert accepted.json()["tripId"] == str(trip_id)
    assert accepted.json()["member"]["role"] == "editor"

    recipient_view = await client.get(f"/api/v1/trips/{trip_id}", headers=recipient_headers)
    assert recipient_view.status_code == 200
    assert recipient_view.json()["title"] == "Kyoto spring"

    second_accept = await client.post(
        "/api/v1/trip-invites/accept",
        json={"code": invite["code"]},
        headers=editor_headers,
    )
    assert second_accept.status_code == 410
