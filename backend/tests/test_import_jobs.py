from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.db import SessionLocal
from app.main import app
from app.models import ImportJob, User
from app.routes import import_jobs
from app.schemas.quick_import import QuickTripEventCandidate
from app.services.jwt_service import issue_token


@pytest_asyncio.fixture
async def import_job_seed():
    async with SessionLocal() as session:
        suffix = uuid4().hex
        owner = User(openid=f"job-owner-{suffix}", nickname=f"Job Owner {suffix[:6]}")
        other = User(openid=f"job-other-{suffix}", nickname=f"Job Other {suffix[:6]}")
        session.add_all([owner, other])
        await session.commit()
        await session.refresh(owner)
        await session.refresh(other)
        data = {
            "owner_id": owner.id,
            "other_id": other.id,
            "owner_token": issue_token(owner.id)[0],
            "other_token": issue_token(other.id)[0],
        }

    try:
        yield data
    finally:
        async with SessionLocal() as session:
            await session.execute(
                delete(User).where(User.id.in_([data["owner_id"], data["other_id"]]))
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
async def test_create_share_import_job_returns_pending_and_schedules(
    client, import_job_seed, monkeypatch
):
    scheduled: list[str] = []

    def fake_schedule(job_id):
        scheduled.append(str(job_id))

    monkeypatch.setattr(import_jobs, "_schedule_share_import_job", fake_schedule)

    response = await client.post(
        "/api/v1/import-jobs/from-share",
        json={"sharedText": "云南旅行分享 http://example.com/share", "type": "long"},
        headers=auth_header(import_job_seed["owner_token"]),
    )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "pending"
    assert data["result"] is None
    assert data["errorMessage"] is None
    assert scheduled == [data["id"]]

    async with SessionLocal() as session:
        job = await session.scalar(select(ImportJob).where(ImportJob.id == data["id"]))
        assert job is not None
        assert job.user_id == import_job_seed["owner_id"]
        assert job.kind == "share_inspiration"
        assert job.shared_text == "云南旅行分享 http://example.com/share"
        assert job.expires_at > datetime.now(UTC)


@pytest.mark.asyncio
async def test_process_share_import_job_stores_success_result(
    client, import_job_seed, monkeypatch
):
    def fake_schedule(job_id):
        return None

    async def fake_extract_share_draft(shared_text: str):
        assert shared_text == "云南路线"
        event = QuickTripEventCandidate(
            clientId="share_1",
            eventType="activity",
            title="逛大理古城",
            startAt=None,
            endAt=None,
            locationName="大理古城",
            address=None,
            latitude=None,
            longitude=None,
            note="适合下午逛吃",
            meta={"dayOffset": 1, "icon": "pin"},
            confidence="high",
            warnings=[],
            sortOrder=0,
        )
        return {
            "destination": "云南",
            "note": "本地人路线",
            "planDetail": "昆明 - 大理 - 丽江",
            "events": [event],
        }, "https://example.com/yunnan"

    monkeypatch.setattr(import_jobs, "_schedule_share_import_job", fake_schedule)
    monkeypatch.setattr(import_jobs, "_extract_share_draft", fake_extract_share_draft)

    created = await client.post(
        "/api/v1/import-jobs/from-share",
        json={"sharedText": "云南路线", "type": "long"},
        headers=auth_header(import_job_seed["owner_token"]),
    )
    assert created.status_code == 202

    await import_jobs._process_share_import_job(created.json()["id"])

    polled = await client.get(
        f"/api/v1/import-jobs/{created.json()['id']}",
        headers=auth_header(import_job_seed["owner_token"]),
    )

    assert polled.status_code == 200
    data = polled.json()
    assert data["status"] == "succeeded"
    assert data["result"]["destination"] == "云南"
    assert data["result"]["sourceUrl"] == "https://example.com/yunnan"
    assert data["result"]["events"][0]["title"] == "逛大理古城"


@pytest.mark.asyncio
async def test_process_share_import_job_stores_readable_failure(
    client, import_job_seed, monkeypatch
):
    def fake_schedule(job_id):
        return None

    async def fake_extract_share_draft(shared_text: str):
        raise HTTPException(status_code=504, detail="整理耗时过长，请稍后重试")

    monkeypatch.setattr(import_jobs, "_schedule_share_import_job", fake_schedule)
    monkeypatch.setattr(import_jobs, "_extract_share_draft", fake_extract_share_draft)

    created = await client.post(
        "/api/v1/import-jobs/from-share",
        json={"sharedText": "云南路线", "type": "long"},
        headers=auth_header(import_job_seed["owner_token"]),
    )
    assert created.status_code == 202

    await import_jobs._process_share_import_job(created.json()["id"])

    polled = await client.get(
        f"/api/v1/import-jobs/{created.json()['id']}",
        headers=auth_header(import_job_seed["owner_token"]),
    )

    assert polled.status_code == 200
    data = polled.json()
    assert data["status"] == "failed"
    assert data["result"] is None
    assert data["errorMessage"] == "整理耗时过长，请稍后重试"


@pytest.mark.asyncio
async def test_get_import_job_marks_expired_job(client, import_job_seed):
    async with SessionLocal() as session:
        job = ImportJob(
            user_id=import_job_seed["owner_id"],
            kind="share_inspiration",
            status="running",
            shared_text="云南路线",
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
            started_at=datetime.now(UTC) - timedelta(minutes=10),
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        job_id = job.id

    polled = await client.get(
        f"/api/v1/import-jobs/{job_id}",
        headers=auth_header(import_job_seed["owner_token"]),
    )

    assert polled.status_code == 200
    data = polled.json()
    assert data["status"] == "expired"
    assert data["errorMessage"] == "任务已超时，请重新导入"


@pytest.mark.asyncio
async def test_import_job_is_scoped_to_owner(client, import_job_seed):
    async with SessionLocal() as session:
        job = ImportJob(
            user_id=import_job_seed["owner_id"],
            kind="share_inspiration",
            status="pending",
            shared_text="云南路线",
            expires_at=datetime.now(UTC) + timedelta(minutes=10),
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        job_id = job.id

    polled = await client.get(
        f"/api/v1/import-jobs/{job_id}",
        headers=auth_header(import_job_seed["other_token"]),
    )

    assert polled.status_code == 404
