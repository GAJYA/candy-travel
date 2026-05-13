# AI Trip Event Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an AI-assisted order screenshot import flow that extracts candidate trip events with `gpt-5.5`, lets the user review them, then saves confirmed events as `source=ai_extracted`.

**Architecture:** CandyTravel backend owns the AI key and exposes two authenticated trip-scoped endpoints: one multipart endpoint for image extraction and one JSON endpoint for confirmed import. The miniapp calls only CandyTravel backend, shows an AI import sheet on the trip edit page, and persists confirmed candidates through the import endpoint.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy async, httpx, pytest-asyncio, uni-app Vue 3, TypeScript.

---

## File Structure

- Modify `backend/pyproject.toml`: add `python-multipart` for FastAPI file uploads.
- Modify `backend/uv.lock`: lock the new upload dependency.
- Modify `backend/app/config.py`: add AI settings with compatibility for current `baseURL` and `apiKey` env names.
- Create `backend/app/schemas/ai_import.py`: request/response DTOs for extraction candidates and import payloads.
- Create `backend/app/services/ai_client.py`: OpenAI-compatible chat completions client, image data-url conversion, timeout handling.
- Create `backend/app/services/ai_trip_event_extractor.py`: prompt construction, AI JSON parsing, candidate validation, sensitive text sanitization.
- Create `backend/app/routes/ai_import.py`: authenticated extraction and import endpoints.
- Modify `backend/app/main.py`: register the AI import router.
- Create `backend/tests/test_ai_trip_event_extractor.py`: unit tests for parsing, schema validation, and sanitization.
- Create `backend/tests/test_ai_trip_event_import.py`: endpoint tests for auth, image validation, trip access, and event creation.
- Create `miniapp/src/services/ai-import.ts`: miniapp API wrapper for upload and import.
- Modify `miniapp/src/pages/edit/index.vue`: add AI import button, image picker, candidate review sheet, and save flow.

## Task 1: Backend Settings And Dependencies

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/uv.lock`
- Modify: `backend/app/config.py`

- [ ] **Step 1: Add multipart dependency**

In `backend/pyproject.toml`, add `python-multipart` to `dependencies`:

```toml
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "sqlalchemy>=2.0",
    "asyncpg>=0.30",
    "alembic>=1.14",
    "pydantic>=2.9",
    "pydantic-settings>=2.6",
    "redis>=5.2",
    "httpx>=0.28",
    "greenlet>=3.5.0",
    "pyjwt>=2.12.1",
    "python-multipart>=0.0.20",
]
```

- [ ] **Step 2: Update dependency lock**

Run:

```bash
cd backend
uv lock
```

Expected: `backend/uv.lock` includes `python-multipart`.

- [ ] **Step 3: Add AI settings**

Replace `backend/app/config.py` with:

```python
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: str = "dev"
    app_version: str = "0.1.0"

    database_url: str = "postgresql+asyncpg://candy:candy@localhost:5432/candy"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me-in-prod"
    jwt_expire_days: int = 7

    wechat_appid: str = ""
    wechat_appsecret: str = ""

    ai_base_url: str = Field(
        default="",
        validation_alias=AliasChoices("AI_BASE_URL", "baseURL"),
    )
    ai_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("AI_API_KEY", "apiKey"),
    )
    ai_model: str = Field(default="gpt-5.5", validation_alias="AI_MODEL")
    ai_timeout_seconds: int = Field(default=60, validation_alias="AI_TIMEOUT_SECONDS")
    ai_max_images: int = Field(default=6, validation_alias="AI_MAX_IMAGES")
    ai_max_image_mb: int = Field(default=8, validation_alias="AI_MAX_IMAGE_MB")
    ai_max_total_image_mb: int = Field(default=24, validation_alias="AI_MAX_TOTAL_IMAGE_MB")


settings = Settings()
```

- [ ] **Step 4: Verify settings load from existing `.env`**

Run:

```bash
cd backend
uv run python - <<'PY'
from app.config import settings
print(settings.ai_base_url)
print(settings.ai_model)
print(bool(settings.ai_api_key))
PY
```

Expected:

```text
https://ai.willer.tech/v1
gpt-5.5
True
```

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock backend/app/config.py
git commit -m "feat: add AI backend settings"
```

## Task 2: AI Import Schemas

**Files:**
- Create: `backend/app/schemas/ai_import.py`
- Test: `backend/tests/test_ai_trip_event_extractor.py`

- [ ] **Step 1: Write failing schema tests**

Create `backend/tests/test_ai_trip_event_extractor.py` with:

```python
import pytest
from pydantic import ValidationError

from app.schemas.ai_import import AiTripEventCandidate


def test_candidate_accepts_transport_payload():
    candidate = AiTripEventCandidate.model_validate(
        {
            "clientId": "tmp_1",
            "eventType": "transport",
            "title": "航班 MU123 上海虹桥 → 东京羽田",
            "startAt": "2026-05-20T09:30:00+08:00",
            "endAt": "2026-05-20T12:45:00+09:00",
            "locationName": "上海虹桥国际机场",
            "address": None,
            "note": "到达：东京羽田机场",
            "meta": {
                "icon": "plane",
                "allDay": False,
                "orderType": "flight",
                "transportMode": "flight",
            },
            "confidence": "high",
            "warnings": [],
        }
    )

    assert candidate.event_type == "transport"
    assert candidate.client_id == "tmp_1"
    assert candidate.confidence == "high"


def test_candidate_rejects_invalid_event_type():
    with pytest.raises(ValidationError):
        AiTripEventCandidate.model_validate(
            {
                "clientId": "tmp_1",
                "eventType": "invoice",
                "title": "发票",
                "startAt": "2026-05-20T09:30:00+08:00",
                "meta": {},
                "confidence": "low",
                "warnings": [],
            }
        )
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
cd backend
uv run pytest tests/test_ai_trip_event_extractor.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.schemas.ai_import'`.

- [ ] **Step 3: Add schema implementation**

Create `backend/app/schemas/ai_import.py`:

```python
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.trip_event import EventType


Confidence = Literal["high", "medium", "low"]


_camel = ConfigDict(populate_by_name=True)


class AiTripEventCandidate(BaseModel):
    model_config = _camel

    client_id: str = Field(validation_alias="clientId", serialization_alias="clientId")
    event_type: EventType = Field(validation_alias="eventType", serialization_alias="eventType")
    title: str = Field(min_length=1, max_length=128)
    start_at: datetime | None = Field(
        default=None,
        validation_alias="startAt",
        serialization_alias="startAt",
    )
    end_at: datetime | None = Field(
        default=None,
        validation_alias="endAt",
        serialization_alias="endAt",
    )
    location_name: str | None = Field(
        default=None,
        max_length=128,
        validation_alias="locationName",
        serialization_alias="locationName",
    )
    address: str | None = Field(default=None, max_length=256)
    note: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    confidence: Confidence = "medium"
    warnings: list[str] = Field(default_factory=list)
    sort_order: int = Field(
        default=0,
        validation_alias="sortOrder",
        serialization_alias="sortOrder",
    )

    @model_validator(mode="after")
    def _check_range(self) -> "AiTripEventCandidate":
        if self.end_at is not None and self.start_at is not None and self.end_at < self.start_at:
            raise ValueError("end_at must be >= start_at")
        return self


class AiExtractEventsResponse(BaseModel):
    model_config = _camel

    trip_id: UUID = Field(serialization_alias="tripId")
    model: str
    events: list[AiTripEventCandidate]
    warnings: list[str] = Field(default_factory=list)


class AiImportEventsIn(BaseModel):
    model_config = _camel

    events: list[AiTripEventCandidate] = Field(min_length=1, max_length=30)
```

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
cd backend
uv run pytest tests/test_ai_trip_event_extractor.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/ai_import.py backend/tests/test_ai_trip_event_extractor.py
git commit -m "feat: add AI trip import schemas"
```

## Task 3: AI Extraction Service

**Files:**
- Create: `backend/app/services/ai_client.py`
- Create: `backend/app/services/ai_trip_event_extractor.py`
- Modify: `backend/tests/test_ai_trip_event_extractor.py`

- [ ] **Step 1: Extend failing extractor tests**

Append to `backend/tests/test_ai_trip_event_extractor.py`:

```python
import json

from app.services.ai_trip_event_extractor import (
    AiExtractionError,
    build_trip_event_prompt,
    parse_ai_event_response,
    sanitize_sensitive_text,
)


def test_parse_ai_event_response_returns_candidates():
    content = json.dumps(
        {
            "events": [
                {
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
                }
            ],
            "warnings": [],
        },
        ensure_ascii=False,
    )

    events, warnings = parse_ai_event_response(content)

    assert warnings == []
    assert events[0].client_id == "tmp_1"
    assert events[0].event_type == "stay"
    assert events[0].meta["icon"] == "hotel"


def test_parse_ai_event_response_rejects_non_json():
    with pytest.raises(AiExtractionError, match="AI returned invalid JSON"):
        parse_ai_event_response("```json\n{}\n```")


def test_sanitize_sensitive_text_masks_personal_data():
    text = "乘机人张三，手机号 13812345678，身份证 110101199001011234，订单金额 1234 元"

    sanitized = sanitize_sensitive_text(text)

    assert "13812345678" not in sanitized
    assert "110101199001011234" not in sanitized
    assert "订单金额" not in sanitized
    assert "乘机人张三" in sanitized


def test_build_trip_event_prompt_contains_trip_context():
    prompt = build_trip_event_prompt(
        trip_title="东京旅行",
        start_date="2026-05-20",
        end_date="2026-05-23",
        timezone="Asia/Tokyo",
    )

    assert "东京旅行" in prompt
    assert "2026-05-20" in prompt
    assert "Asia/Tokyo" in prompt
    assert "只返回 JSON" in prompt
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
cd backend
uv run pytest tests/test_ai_trip_event_extractor.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.ai_trip_event_extractor'`.

- [ ] **Step 3: Add extractor service**

Create `backend/app/services/ai_trip_event_extractor.py`:

```python
from __future__ import annotations

import json
import re
from datetime import date
from typing import Any

from pydantic import ValidationError

from app.schemas.ai_import import AiTripEventCandidate


class AiExtractionError(Exception):
    """Raised when the AI response cannot be converted into trip event candidates."""


_PHONE_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
_ID_CARD_RE = re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")
_AMOUNT_RE = re.compile(r"(订单金额|支付金额|实付|总价|票价)[:：]?\s*[0-9.,]+元?")


def sanitize_sensitive_text(text: str | None) -> str | None:
    if not text:
        return text
    sanitized = _PHONE_RE.sub("[手机号已省略]", text)
    sanitized = _ID_CARD_RE.sub("[身份证号已省略]", sanitized)
    sanitized = _AMOUNT_RE.sub("[金额已省略]", sanitized)
    return sanitized


def build_trip_event_prompt(
    *,
    trip_title: str,
    start_date: date | str | None,
    end_date: date | str | None,
    timezone: str,
) -> str:
    return f"""
你是 CandyTravel 的订单截图识别助手。请从用户上传的飞机、高铁、酒店订单截图中提取可以加入旅行日程的事件。

当前行程：
- 标题：{trip_title}
- 开始日期：{start_date or "未设置"}
- 结束日期：{end_date or "未设置"}
- 默认时区：{timezone}

要求：
- 只返回 JSON，不输出 Markdown，不要包裹代码块。
- 忽略身份证、手机号、支付金额、银行卡号、完整订单号等敏感信息。
- 优先识别飞机、高铁、酒店订单。
- 缺少日期、时间或地点时仍可返回候选项，但 warnings 必须说明缺失字段，confidence 使用 low 或 medium。
- 时间必须使用 ISO 8601 字符串，并尽量带上截图或行程能推断出的时区。
- 酒店入住事件使用全天事件，startAt 为入住日 00:00，endAt 为离店日 00:00。

返回格式：
{{
  "events": [
    {{
      "eventType": "transport|stay|activity|reminder",
      "title": "事件标题",
      "startAt": "ISO8601 或 null",
      "endAt": "ISO8601 或 null",
      "locationName": "地点名或 null",
      "address": "地址或 null",
      "note": "非敏感摘要或 null",
      "meta": {{
        "icon": "plane|train|hotel|ticket|clock|pin",
        "allDay": false,
        "orderType": "flight|train|hotel|other"
      }},
      "confidence": "high|medium|low",
      "warnings": []
    }}
  ],
  "warnings": []
}}
""".strip()


def parse_ai_event_response(content: str) -> tuple[list[AiTripEventCandidate], list[str]]:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as e:
        raise AiExtractionError("AI returned invalid JSON") from e

    if not isinstance(payload, dict):
        raise AiExtractionError("AI response must be a JSON object")

    raw_events = payload.get("events")
    if not isinstance(raw_events, list):
        raise AiExtractionError("AI response missing events list")

    events: list[AiTripEventCandidate] = []
    for index, raw_event in enumerate(raw_events, start=1):
        if not isinstance(raw_event, dict):
            raise AiExtractionError("AI event must be a JSON object")
        event_data: dict[str, Any] = {
            **raw_event,
            "clientId": raw_event.get("clientId") or f"tmp_{index}",
            "note": sanitize_sensitive_text(raw_event.get("note")),
        }
        try:
            events.append(AiTripEventCandidate.model_validate(event_data))
        except ValidationError as e:
            raise AiExtractionError(f"AI event {index} failed validation") from e

    warnings = payload.get("warnings") or []
    if not isinstance(warnings, list):
        warnings = ["AI returned warnings in an invalid format"]
    return events, [str(item) for item in warnings]
```

- [ ] **Step 4: Add AI client**

Create `backend/app/services/ai_client.py`:

```python
from __future__ import annotations

import base64

import httpx

from app.config import settings


class AiClientError(Exception):
    """Raised when the OpenAI-compatible AI endpoint fails."""


class AiClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self.base_url = (base_url or settings.ai_base_url).rstrip("/")
        self.api_key = api_key or settings.ai_api_key
        self.model = model or settings.ai_model
        self.timeout_seconds = timeout_seconds or settings.ai_timeout_seconds

    async def describe_images(self, *, prompt: str, images: list[tuple[bytes, str]]) -> str:
        if not self.base_url or not self.api_key:
            raise AiClientError("AI service is not configured")
        if not images:
            raise AiClientError("at least one image is required")

        content: list[dict[str, object]] = [{"type": "text", "text": prompt}]
        for image_bytes, media_type in images:
            encoded = base64.b64encode(image_bytes).decode("ascii")
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{media_type};base64,{encoded}"},
                }
            )

        payload = {
            "model": self.model,
            "stream": False,
            "messages": [{"role": "user", "content": content}],
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
        except httpx.TimeoutException as e:
            raise AiClientError("AI request timed out") from e
        except httpx.HTTPStatusError as e:
            raise AiClientError(f"AI request failed with HTTP {e.response.status_code}") from e
        except httpx.HTTPError as e:
            raise AiClientError("AI request failed") from e

        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise AiClientError("AI response missing message content") from e
```

- [ ] **Step 5: Run tests to verify GREEN**

Run:

```bash
cd backend
uv run pytest tests/test_ai_trip_event_extractor.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/ai_client.py backend/app/services/ai_trip_event_extractor.py backend/tests/test_ai_trip_event_extractor.py
git commit -m "feat: add AI trip event extractor"
```

## Task 4: AI Import Backend Routes

**Files:**
- Create: `backend/app/routes/ai_import.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_ai_trip_event_import.py`

- [ ] **Step 1: Write failing endpoint tests**

Create `backend/tests/test_ai_trip_event_import.py`:

```python
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
            await session.execute(delete(User).where(User.id.in_([data["owner_id"], data["stranger_id"]])))
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
        return (
            [
                AiTripEventCandidate.model_validate(
                    {
                        "clientId": "tmp_1",
                        "eventType": "transport",
                        "title": "航班 MU123 上海虹桥 → 东京羽田",
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
    assert body["events"][0]["title"] == "航班 MU123 上海虹桥 → 东京羽田"


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
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
cd backend
uv run pytest tests/test_ai_trip_event_import.py -q
```

Expected: FAIL with 404 for the new `/ai/extract-events` route.

- [ ] **Step 3: Add route implementation**

Create `backend/app/routes/ai_import.py`:

```python
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.config import settings
from app.deps import CurrentUser, SessionDep
from app.models import TripEvent
from app.schemas.ai_import import AiExtractEventsResponse, AiImportEventsIn
from app.schemas.trip_event import TripEventOut
from app.services.ai_client import AiClientError
from app.services.ai_trip_event_extractor import AiExtractionError, extract_trip_events
from app.services.trip_access import get_accessible_trip

router = APIRouter(tags=["ai-import"])

SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


async def _read_images(files: list[UploadFile]) -> list[tuple[bytes, str]]:
    if not files:
        raise HTTPException(status_code=400, detail="at least one image is required")
    if len(files) > settings.ai_max_images:
        raise HTTPException(status_code=400, detail="too many images")

    max_image_bytes = settings.ai_max_image_mb * 1024 * 1024
    max_total_bytes = settings.ai_max_total_image_mb * 1024 * 1024
    total = 0
    images: list[tuple[bytes, str]] = []

    for file in files:
        media_type = file.content_type or ""
        if media_type not in SUPPORTED_IMAGE_TYPES:
            raise HTTPException(status_code=400, detail="unsupported image type")
        data = await file.read()
        if len(data) > max_image_bytes:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="image too large")
        total += len(data)
        if total > max_total_bytes:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="images too large")
        images.append((data, media_type))

    return images


@router.post(
    "/trips/{trip_id}/ai/extract-events",
    response_model=AiExtractEventsResponse,
    response_model_by_alias=True,
)
async def extract_events(
    trip_id: UUID,
    user: CurrentUser,
    session: SessionDep,
    images: Annotated[list[UploadFile], File()],
    client_timezone: Annotated[str | None, Form(alias="clientTimezone")] = None,
) -> AiExtractEventsResponse:
    trip = await get_accessible_trip(session, user_id=user.id, trip_id=trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="trip not found")

    image_payloads = await _read_images(images)
    try:
        events, warnings, model = await extract_trip_events(
            trip=trip,
            images=image_payloads,
            client_timezone=client_timezone,
        )
    except AiExtractionError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except AiClientError as e:
        detail = str(e)
        status_code = 504 if "timed out" in detail else 502
        raise HTTPException(status_code=status_code, detail=detail) from e

    return AiExtractEventsResponse(
        trip_id=trip.id,
        model=model,
        events=events,
        warnings=warnings,
    )


@router.post(
    "/trips/{trip_id}/ai/import-events",
    response_model=list[TripEventOut],
    response_model_by_alias=True,
    status_code=201,
)
async def import_events(
    trip_id: UUID,
    payload: AiImportEventsIn,
    user: CurrentUser,
    session: SessionDep,
) -> list[TripEventOut]:
    trip = await get_accessible_trip(session, user_id=user.id, trip_id=trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="trip not found")

    created: list[TripEvent] = []
    for candidate in payload.events:
        if candidate.start_at is None:
            raise HTTPException(status_code=400, detail="startAt is required")
        event = TripEvent(
            user_id=user.id,
            trip_id=trip.id,
            event_type=candidate.event_type.value,
            title=candidate.title,
            start_at=candidate.start_at,
            end_at=candidate.end_at,
            location_name=candidate.location_name,
            address=candidate.address,
            note=candidate.note,
            meta={
                **candidate.meta,
                "ai": {
                    "clientId": candidate.client_id,
                    "confidence": candidate.confidence,
                    "warnings": candidate.warnings,
                },
            },
            status="confirmed",
            source="ai_extracted",
            sort_order=candidate.sort_order,
        )
        session.add(event)
        created.append(event)

    await session.commit()
    for event in created:
        await session.refresh(event)
    return [TripEventOut.model_validate(event) for event in created]
```

- [ ] **Step 4: Add service orchestration function**

Append this function to `backend/app/services/ai_trip_event_extractor.py`:

```python
from app.config import settings
from app.models import Trip
from app.services.ai_client import AiClient


async def extract_trip_events(
    *,
    trip: Trip,
    images: list[tuple[bytes, str]],
    client_timezone: str | None = None,
) -> tuple[list[AiTripEventCandidate], list[str], str]:
    timezone = client_timezone or trip.timezone or "Asia/Shanghai"
    prompt = build_trip_event_prompt(
        trip_title=trip.title,
        start_date=trip.start_date,
        end_date=trip.end_date,
        timezone=timezone,
    )
    client = AiClient(model=settings.ai_model)
    content = await client.describe_images(prompt=prompt, images=images)
    events, warnings = parse_ai_event_response(content)
    return events, warnings, client.model
```

- [ ] **Step 5: Register route in FastAPI**

Modify `backend/app/main.py` imports:

```python
from app.routes import ai_import, auth, checklist, health, me, trip_events, trip_invites, trips
```

Add router registration after trip event routes:

```python
app.include_router(ai_import.router, prefix=api_v1)
```

- [ ] **Step 6: Run endpoint tests to verify GREEN**

Run:

```bash
cd backend
uv run pytest tests/test_ai_trip_event_import.py -q
```

Expected: PASS.

- [ ] **Step 7: Run existing backend tests**

Run:

```bash
cd backend
uv run pytest -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/app/routes/ai_import.py backend/app/main.py backend/app/services/ai_trip_event_extractor.py backend/tests/test_ai_trip_event_import.py
git commit -m "feat: add AI trip event import endpoints"
```

## Task 5: Miniapp AI Import Service

**Files:**
- Create: `miniapp/src/services/ai-import.ts`

- [ ] **Step 1: Add service types and upload wrapper**

Create `miniapp/src/services/ai-import.ts`:

```typescript
import { apiBaseUrl, request, tokenStorage } from './api'

export type AiEventConfidence = 'high' | 'medium' | 'low'
export type AiEventType = 'transport' | 'stay' | 'activity' | 'reminder'

export interface AiTripEventCandidate {
  clientId: string
  eventType: AiEventType
  title: string
  startAt: string | null
  endAt: string | null
  locationName: string | null
  address: string | null
  note: string | null
  meta: Record<string, unknown>
  confidence: AiEventConfidence
  warnings: string[]
  sortOrder: number
}

export interface AiExtractEventsResponse {
  tripId: string
  model: string
  events: AiTripEventCandidate[]
  warnings: string[]
}

const uploadOneImage = (tripId: string, filePath: string): Promise<AiExtractEventsResponse> => {
  const token = tokenStorage.get()
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${apiBaseUrl}/trips/${tripId}/ai/extract-events`,
      filePath,
      name: 'images',
      header: token ? { Authorization: `Bearer ${token}` } : {},
      formData: {},
      success: (res) => {
        const status = res.statusCode ?? 0
        if (status >= 200 && status < 300) {
          try {
            resolve(JSON.parse(res.data) as AiExtractEventsResponse)
          } catch {
            reject(new Error('识别结果解析失败'))
          }
          return
        }
        reject(new Error(`识别失败：HTTP ${status}`))
      },
      fail: (err) => reject(new Error(err.errMsg || '图片上传失败')),
    })
  })
}

export const aiImportApi = {
  async extractTripEvents(tripId: string, filePaths: string[]): Promise<AiExtractEventsResponse> {
    const responses: AiExtractEventsResponse[] = []
    for (const filePath of filePaths) {
      responses.push(await uploadOneImage(tripId, filePath))
    }
    return {
      tripId,
      model: responses[0]?.model || 'gpt-5.5',
      events: responses.flatMap((response, responseIndex) => (
        response.events.map((event, eventIndex) => ({
          ...event,
          clientId: `${event.clientId}-${responseIndex}-${eventIndex}`,
          sortOrder: event.sortOrder ?? eventIndex,
        }))
      )),
      warnings: responses.flatMap((response) => response.warnings || []),
    }
  },

  importTripEvents: (tripId: string, events: AiTripEventCandidate[]) =>
    request(`/trips/${tripId}/ai/import-events`, {
      method: 'POST',
      data: { events },
    }),
}
```

- [ ] **Step 2: Type-check**

Run:

```bash
cd miniapp
npm run type-check
```

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add miniapp/src/services/ai-import.ts
git commit -m "feat: add miniapp AI import service"
```

## Task 6: Miniapp Review UI

**Files:**
- Modify: `miniapp/src/pages/edit/index.vue`

- [ ] **Step 1: Add imports and state**

In `miniapp/src/pages/edit/index.vue`, extend imports:

```typescript
import {
  aiImportApi,
  type AiTripEventCandidate,
} from '../../services/ai-import'
```

Add state near existing modal state:

```typescript
const aiImportOpen = ref(false)
const aiImportReviewOpen = ref(false)
const aiImportLoading = ref(false)
const aiImportCandidates = ref<AiTripEventCandidate[]>([])
const aiImportWarnings = ref<string[]>([])
```

- [ ] **Step 2: Add AI import button beside Add Event**

Replace the “每日行程” action area with two buttons:

```vue
<view class="section-actions">
  <button
    class="mini-action mini-action--secondary"
    :disabled="!tripId"
    @click="onShowAiImport"
  >
    AI导入
  </button>
  <button
    class="mini-action"
    :disabled="!tripId"
    @click="onShowEventAdd"
  >
    ＋ 添加事件
  </button>
</view>
```

- [ ] **Step 3: Add upload modal template**

Insert before the existing “添加事件弹层”:

```vue
<view v-if="aiImportOpen" class="modal-mask" @click="aiImportOpen = false">
  <view class="modal" @click.stop>
    <text class="modal-title">AI 补充行程</text>
    <view class="ai-import-card">
      <view class="ai-import-card__icon">
        <CandyIcon name="sparkle" />
      </view>
      <view class="ai-import-card__copy">
        <text class="ai-import-card__title">上传订单截图</text>
        <text class="ai-import-card__hint">支持飞机、高铁、酒店订单截图。图片仅用于本次识别，不会保存。</text>
      </view>
    </view>
    <view class="modal-actions">
      <button class="candy-btn candy-btn--ghost" :disabled="aiImportLoading" @click="aiImportOpen = false">取消</button>
      <button class="candy-btn candy-btn--primary" :disabled="aiImportLoading" @click="onChooseAiImportImages">
        {{ aiImportLoading ? '识别中…' : '选择截图' }}
      </button>
    </view>
  </view>
</view>
```

- [ ] **Step 4: Add review modal template**

Insert after the upload modal:

```vue
<view v-if="aiImportReviewOpen" class="modal-mask" @click="aiImportReviewOpen = false">
  <view class="modal modal--event" @click.stop>
    <text class="modal-title">识别到 {{ aiImportCandidates.length }} 个行程事件</text>
    <scroll-view class="event-modal-scroll" scroll-y :show-scrollbar="false">
      <view class="ai-candidate-list">
        <view v-for="candidate in aiImportCandidates" :key="candidate.clientId" class="ai-candidate-card">
          <view class="ai-candidate-card__head">
            <view class="event-icon-badge">
              <CandyIcon :name="normalizeIconName(candidate.meta?.icon, 'sparkle')" />
            </view>
            <view class="ai-candidate-card__copy">
              <text class="event-title">{{ candidate.title }}</text>
              <text class="event-meta">{{ candidateTimeLabel(candidate) }}</text>
              <text v-if="candidate.locationName" class="event-meta">地点：{{ candidate.locationName }}</text>
              <text class="event-meta">置信度：{{ confidenceLabel(candidate.confidence) }}</text>
              <text v-if="candidate.warnings.length" class="candy-text-error">{{ candidate.warnings.join('；') }}</text>
            </view>
          </view>
          <view class="ai-candidate-card__actions">
            <button class="mini-action mini-action--secondary" @click="onEditAiCandidate(candidate)">编辑</button>
            <button class="mini-action mini-action--secondary" @click="onRemoveAiCandidate(candidate.clientId)">移除</button>
          </view>
        </view>
      </view>
    </scroll-view>
    <view class="modal-actions">
      <button class="candy-btn candy-btn--ghost" :disabled="aiImportLoading" @click="aiImportReviewOpen = false">取消</button>
      <button class="candy-btn candy-btn--primary" :disabled="!canSaveAiCandidates || aiImportLoading" @click="onSaveAiCandidates">
        {{ aiImportLoading ? '保存中…' : '保存到行程' }}
      </button>
    </view>
  </view>
</view>
```

- [ ] **Step 5: Add UI methods**

Add these methods near event methods:

```typescript
const onShowAiImport = async () => {
  if (!tripId.value) {
    uni.showToast({ title: '请先保存行程', icon: 'none' })
    return
  }
  if (hasUnsavedChanges()) {
    uni.showToast({ title: '请先保存当前行程', icon: 'none' })
    return
  }
  aiImportOpen.value = true
}

const onChooseAiImportImages = () => {
  if (aiImportLoading.value) return
  uni.chooseImage({
    count: 6,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      const paths = res.tempFilePaths || []
      if (!paths.length) return
      void extractAiImportImages(paths)
    },
  })
}

const extractAiImportImages = async (paths: string[]) => {
  aiImportLoading.value = true
  try {
    const result = await aiImportApi.extractTripEvents(tripId.value, paths)
    aiImportCandidates.value = result.events
    aiImportWarnings.value = result.warnings
    aiImportOpen.value = false
    if (!result.events.length) {
      uni.showToast({ title: '未识别到可导入的行程信息', icon: 'none' })
      return
    }
    aiImportReviewOpen.value = true
  } catch (e) {
    uni.showToast({ title: e instanceof Error ? e.message : '识别失败', icon: 'none' })
  } finally {
    aiImportLoading.value = false
  }
}

const candidateTimeLabel = (candidate: AiTripEventCandidate) => {
  if (!candidate.startAt) return '时间待补充'
  if (candidate.meta?.allDay === true) return datePart(candidate.startAt)
  const start = `${datePart(candidate.startAt)} ${formatEventTime(candidate.startAt)}`
  if (!candidate.endAt) return start
  return `${start} - ${formatEventTime(candidate.endAt)}`
}

const confidenceLabel = (confidence: string) => (
  { high: '高', medium: '中', low: '低' }[confidence] || '中'
)

const canSaveAiCandidates = computed(() => (
  aiImportCandidates.value.length > 0
  && aiImportCandidates.value.every((candidate) => Boolean(candidate.title.trim() && candidate.startAt))
))

const onRemoveAiCandidate = (clientId: string) => {
  aiImportCandidates.value = aiImportCandidates.value.filter((candidate) => candidate.clientId !== clientId)
}

const onEditAiCandidate = (candidate: AiTripEventCandidate) => {
  eventEditingId.value = `ai:${candidate.clientId}`
  eventForm.icon = normalizeIconName(candidate.meta?.icon, 'sparkle')
  eventForm.title = candidate.title
  eventForm.date = candidate.startAt ? datePart(candidate.startAt) : (form.departDate || datePart(new Date().toISOString()))
  eventForm.allDay = candidate.meta?.allDay === true
  eventForm.startTime = candidate.startAt && !eventForm.allDay ? formatEventTime(candidate.startAt) : ''
  eventForm.endTime = candidate.endAt && !eventForm.allDay ? formatEventTime(candidate.endAt) : ''
  eventForm.locationName = candidate.locationName || ''
  eventForm.note = candidate.note || ''
  eventAddOpen.value = true
}

const updateAiCandidateFromEventForm = (clientId: string) => {
  const startAt = buildIsoDateTime(eventForm.date, eventForm.startTime)
  const endAt = !eventForm.allDay && eventForm.endTime ? buildIsoDateTime(eventForm.date, eventForm.endTime) : null
  aiImportCandidates.value = aiImportCandidates.value.map((candidate) => {
    if (candidate.clientId !== clientId) return candidate
    return {
      ...candidate,
      title: eventForm.title.trim(),
      startAt,
      endAt,
      locationName: eventForm.locationName.trim() || null,
      note: eventForm.note.trim() || null,
      meta: { ...candidate.meta, icon: eventForm.icon, allDay: eventForm.allDay },
      warnings: startAt ? candidate.warnings : [...candidate.warnings, '缺少开始时间'],
    }
  })
}

const onSaveAiCandidates = async () => {
  if (!canSaveAiCandidates.value || aiImportLoading.value) return
  aiImportLoading.value = true
  try {
    await aiImportApi.importTripEvents(tripId.value, aiImportCandidates.value)
    await loadEvents()
    aiImportReviewOpen.value = false
    aiImportCandidates.value = []
    uni.showToast({ title: '已导入行程', icon: 'success' })
  } catch (e) {
    uni.showToast({ title: e instanceof Error ? e.message : '保存失败', icon: 'none' })
  } finally {
    aiImportLoading.value = false
  }
}
```

- [ ] **Step 6: Patch event submit for AI candidate edits**

At the start of `onEventAddSubmit`, after validation and `startAt` calculation, insert:

```typescript
  if (eventEditingId.value.startsWith('ai:')) {
    updateAiCandidateFromEventForm(eventEditingId.value.slice(3))
    eventAddOpen.value = false
    eventEditingId.value = ''
    uni.showToast({ title: '已更新候选项', icon: 'success' })
    return
  }
```

- [ ] **Step 7: Add minimal styles**

Append to the `<style>` block:

```scss
.section-actions {
  display: flex;
  flex-direction: row;
  gap: 12rpx;
}

.ai-import-card {
  display: flex;
  flex-direction: row;
  gap: 18rpx;
  padding: 22rpx;
  border-radius: $candy-radius-lg;
  background: $candy-surface-container-low;
}

.ai-import-card__icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: $candy-radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  color: $candy-primary;
  background: $candy-primary-container;
}

.ai-import-card__copy {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.ai-import-card__title {
  font-size: $candy-font-title-sm;
  font-weight: 800;
  color: $candy-on-surface;
}

.ai-import-card__hint {
  font-size: $candy-font-body-sm;
  color: $candy-on-surface-variant;
  line-height: 1.5;
}

.ai-candidate-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.ai-candidate-card {
  padding: 18rpx;
  border-radius: $candy-radius-lg;
  background: $candy-surface-container-low;
}

.ai-candidate-card__head {
  display: flex;
  flex-direction: row;
  gap: 16rpx;
}

.ai-candidate-card__copy {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.ai-candidate-card__actions {
  margin-top: 16rpx;
  display: flex;
  flex-direction: row;
  justify-content: flex-end;
  gap: 12rpx;
}
```

- [ ] **Step 8: Type-check**

Run:

```bash
cd miniapp
npm run type-check
```

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add miniapp/src/pages/edit/index.vue
git commit -m "feat: add AI import review UI"
```

## Task 7: End-To-End Verification

**Files:**
- No planned source changes.

- [ ] **Step 1: Run backend tests**

```bash
cd backend
uv run pytest -q
```

Expected: PASS.

- [ ] **Step 2: Run backend lint**

```bash
cd backend
uv run ruff check .
```

Expected: PASS.

- [ ] **Step 3: Run miniapp type-check**

```bash
cd miniapp
npm run type-check
```

Expected: PASS.

- [ ] **Step 4: Manual AI smoke test**

Run backend locally with the real `.env`, then upload a known order screenshot from the miniapp dev build. If no order screenshot is available, use a clear image containing a flight or hotel order from a test account.

Expected:

- `AI导入` opens the upload sheet.
- Selecting one image returns at least one candidate for a valid order screenshot.
- Editing a candidate updates the review list.
- Saving creates events visible in “每日行程”.
- Network or AI failure does not create any event.

- [ ] **Step 5: Commit verification notes if source changed during fixes**

If verification required code fixes:

```bash
git add backend miniapp
git commit -m "fix: stabilize AI import flow"
```

If no fixes were needed, do not create an empty commit.
