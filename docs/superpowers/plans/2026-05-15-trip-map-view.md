# Trip Map View Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a coordinate-backed trip map tab that connects itinerary events in the current time order and lets users bind coordinates through map place selection.

**Architecture:** Coordinates live on `trip_events` as nullable `latitude` and `longitude` columns, with API validation enforcing complete coordinate pairs. The miniapp keeps location display text editable, stores coordinates only when the user uses map selection, and derives map markers, polyline, and missing-location prompts from the event list.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic v2, pytest/httpx, uni-app, Vue 3, TypeScript, WeChat mini program `<map>`, `uni.chooseLocation`.

---

## File Structure

- Create: `backend/tests/test_trip_event_coordinates.py`
  - Covers event coordinate create/list/patch validation and AI import coordinate persistence.
- Create: `backend/alembic/versions/0009_trip_event_coordinates.py`
  - Adds `latitude` and `longitude` columns and database constraints.
- Modify: `backend/app/models/trip_event.py`
  - Adds coordinate columns and model-level check constraints.
- Modify: `backend/app/schemas/trip_event.py`
  - Adds coordinate fields and Pydantic pair/range validation for create, patch, and output.
- Modify: `backend/app/routes/trip_events.py`
  - Persists coordinates on regular event creation and patch.
- Modify: `backend/app/schemas/ai_import.py`
  - Lets edited AI candidates carry coordinates.
- Modify: `backend/app/routes/ai_import.py`
  - Persists candidate coordinates into created `TripEvent` rows.
- Modify: `miniapp/src/services/trip-event.ts`
  - Adds coordinate fields to event API types.
- Modify: `miniapp/src/services/ai-import.ts`
  - Adds coordinate fields to AI candidate types so edited candidates can import coordinates.
- Create: `miniapp/src/utils/trip-map.ts`
  - Pure map data builder for markers, polyline, map center, and missing-location list.
- Modify: `miniapp/src/pages/edit/index.vue`
  - Adds `日程 / 地图 / 清单` tab UI, map panel, location picker button, coordinate-aware event form state, and submit payload updates.

---

### Task 1: Backend Coordinate API Tests

**Files:**
- Create: `backend/tests/test_trip_event_coordinates.py`

- [ ] **Step 1: Write failing coordinate API tests**

Create `backend/tests/test_trip_event_coordinates.py`:

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
    assert created_body["latitude"] == 30.24258
    assert created_body["longitude"] == 120.15062

    listed = await client.get(
        f"/api/v1/trips/{coordinate_trip_seed['trip_id']}/events",
        headers=headers,
    )

    assert listed.status_code == 200
    assert listed.json()[0]["latitude"] == 30.24258
    assert listed.json()[0]["longitude"] == 120.15062


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
async def test_rejects_incomplete_or_out_of_range_coordinates(client, coordinate_trip_seed):
    headers = auth_header(coordinate_trip_seed["owner_token"])

    incomplete = await client.post(
        f"/api/v1/trips/{coordinate_trip_seed['trip_id']}/events",
        json={
            "eventType": "activity",
            "title": "只有纬度",
            "startAt": "2026-06-01T08:30:00Z",
            "latitude": 30.27,
            "meta": {"icon": "pin", "allDay": False},
        },
        headers=headers,
    )
    assert incomplete.status_code == 422

    out_of_range = await client.post(
        f"/api/v1/trips/{coordinate_trip_seed['trip_id']}/events",
        json={
            "eventType": "activity",
            "title": "非法纬度",
            "startAt": "2026-06-01T09:00:00Z",
            "latitude": 91,
            "longitude": 120.15,
            "meta": {"icon": "pin", "allDay": False},
        },
        headers=headers,
    )
    assert out_of_range.status_code == 422


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
```

- [ ] **Step 2: Run coordinate tests and confirm they fail before implementation**

Run:

```bash
cd backend && uv run pytest tests/test_trip_event_coordinates.py -q
```

Expected: failure because `TripEventOut` responses do not contain `latitude` or `longitude`, and coordinate validation is not implemented.

- [ ] **Step 3: Commit failing tests**

```bash
git add backend/tests/test_trip_event_coordinates.py
git commit -m "test: cover trip event coordinates"
```

---

### Task 2: Backend Coordinate Storage and Validation

**Files:**
- Create: `backend/alembic/versions/0009_trip_event_coordinates.py`
- Modify: `backend/app/models/trip_event.py`
- Modify: `backend/app/schemas/trip_event.py`
- Modify: `backend/app/routes/trip_events.py`
- Modify: `backend/app/schemas/ai_import.py`
- Modify: `backend/app/routes/ai_import.py`

- [ ] **Step 1: Add Alembic migration**

Create `backend/alembic/versions/0009_trip_event_coordinates.py`:

```python
"""add coordinates to trip_events

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-15

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("trip_events", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("trip_events", sa.Column("longitude", sa.Float(), nullable=True))
    op.create_check_constraint(
        "ck_trip_events_coordinate_pair",
        "trip_events",
        "(latitude IS NULL AND longitude IS NULL) OR "
        "(latitude IS NOT NULL AND longitude IS NOT NULL)",
    )
    op.create_check_constraint(
        "ck_trip_events_latitude_range",
        "trip_events",
        "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
    )
    op.create_check_constraint(
        "ck_trip_events_longitude_range",
        "trip_events",
        "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_trip_events_longitude_range",
        "trip_events",
        type_="check",
    )
    op.drop_constraint(
        "ck_trip_events_latitude_range",
        "trip_events",
        type_="check",
    )
    op.drop_constraint(
        "ck_trip_events_coordinate_pair",
        "trip_events",
        type_="check",
    )
    op.drop_column("trip_events", "longitude")
    op.drop_column("trip_events", "latitude")
```

- [ ] **Step 2: Update SQLAlchemy model**

In `backend/app/models/trip_event.py`, add `Float` to the SQLAlchemy imports:

```python
    Float,
```

Add these columns after `address`:

```python
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
```

Add these constraints inside `__table_args__` before indexes:

```python
        CheckConstraint(
            "(latitude IS NULL AND longitude IS NULL) OR "
            "(latitude IS NOT NULL AND longitude IS NOT NULL)",
            name="ck_trip_events_coordinate_pair",
        ),
        CheckConstraint(
            "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
            name="ck_trip_events_latitude_range",
        ),
        CheckConstraint(
            "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
            name="ck_trip_events_longitude_range",
        ),
```

- [ ] **Step 3: Update trip event schemas**

In `backend/app/schemas/trip_event.py`, add coordinate fields to `TripEventCreate`, `TripEventPatch`, and `TripEventOut`.

For `TripEventCreate`, insert after `address`:

```python
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
```

Replace `TripEventCreate._check_range` with:

```python
    @model_validator(mode="after")
    def _check_values(self) -> "TripEventCreate":
        if self.end_at and self.end_at < self.start_at:
            raise ValueError("end_at must be >= start_at")
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be provided together")
        return self
```

For `TripEventPatch`, insert after `address`:

```python
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @model_validator(mode="after")
    def _check_coordinates(self) -> "TripEventPatch":
        fields_set = self.model_fields_set
        latitude_set = "latitude" in fields_set
        longitude_set = "longitude" in fields_set
        if latitude_set != longitude_set:
            raise ValueError("latitude and longitude must be patched together")
        if latitude_set and longitude_set and (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be provided together")
        return self
```

For `TripEventOut`, insert after `address`:

```python
    latitude: float | None
    longitude: float | None
```

- [ ] **Step 4: Persist coordinates in regular event routes**

In `backend/app/routes/trip_events.py`, add these fields to the `TripEvent(...)` constructor in `create_event` after `address=payload.address`:

```python
        latitude=payload.latitude,
        longitude=payload.longitude,
```

No loop change is needed in `patch_event`; `payload.model_dump(exclude_unset=True)` will update coordinates only when the client explicitly sends them.

- [ ] **Step 5: Carry coordinates through AI import**

In `backend/app/schemas/ai_import.py`, add fields after `address` in `AiTripEventCandidate`:

```python
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
```

Replace `AiTripEventCandidate._check_range` with:

```python
    @model_validator(mode="after")
    def _check_values(self) -> "AiTripEventCandidate":
        if self.end_at is not None and self.start_at is not None and self.end_at < self.start_at:
            raise ValueError("end_at must be >= start_at")
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be provided together")
        return self
```

In `backend/app/routes/ai_import.py`, add these fields to the `TripEvent(...)` constructor after `address=candidate.address`:

```python
            latitude=candidate.latitude,
            longitude=candidate.longitude,
```

- [ ] **Step 6: Apply database migration locally**

Run:

```bash
cd backend && uv run alembic upgrade head
```

Expected: migration reaches revision `0009` without errors.

- [ ] **Step 7: Run backend coordinate tests**

Run:

```bash
cd backend && uv run pytest tests/test_trip_event_coordinates.py -q
```

Expected: all tests in `test_trip_event_coordinates.py` pass.

- [ ] **Step 8: Run existing backend regression tests**

Run:

```bash
cd backend && uv run pytest tests/test_ai_trip_event_import.py tests/test_trip_sharing.py -q
```

Expected: all selected tests pass.

- [ ] **Step 9: Run backend lint**

Run:

```bash
cd backend && uv run ruff check app tests
```

Expected: no lint errors.

- [ ] **Step 10: Commit backend implementation**

```bash
git add backend/alembic/versions/0009_trip_event_coordinates.py backend/app/models/trip_event.py backend/app/schemas/trip_event.py backend/app/routes/trip_events.py backend/app/schemas/ai_import.py backend/app/routes/ai_import.py
git commit -m "feat: store trip event coordinates"
```

---

### Task 3: Frontend Event Types and Map Data Helper

**Files:**
- Modify: `miniapp/src/services/trip-event.ts`
- Modify: `miniapp/src/services/ai-import.ts`
- Create: `miniapp/src/utils/trip-map.ts`

- [ ] **Step 1: Add coordinate fields to miniapp event API types**

In `miniapp/src/services/trip-event.ts`, add fields to `TripEvent` after `address`:

```ts
  latitude: number | null
  longitude: number | null
```

Add fields to `TripEventCreatePayload` after `address`:

```ts
  latitude?: number | null
  longitude?: number | null
```

Add fields to `TripEventPatchPayload` after `address`:

```ts
  latitude?: number | null
  longitude?: number | null
```

- [ ] **Step 2: Add coordinate fields to AI candidate type**

In `miniapp/src/services/ai-import.ts`, add fields to `AiTripEventCandidate` after `address`:

```ts
  latitude: number | null
  longitude: number | null
```

In `extractTripEvents`, keep the spread and normalize missing coordinates while mapping events:

```ts
          latitude: event.latitude ?? null,
          longitude: event.longitude ?? null,
```

- [ ] **Step 3: Create map data helper**

Create `miniapp/src/utils/trip-map.ts`:

```ts
import type { TripEvent } from '../services/trip-event'

export interface TripMapPoint {
  latitude: number
  longitude: number
}

export interface TripMapMarker extends TripMapPoint {
  id: number
  title: string
  callout: {
    content: string
    color: string
    fontSize: number
    borderRadius: number
    bgColor: string
    padding: number
    display: 'ALWAYS'
  }
}

export interface TripMapPolyline {
  points: TripMapPoint[]
  color: string
  width: number
  dottedLine: boolean
  arrowLine: boolean
}

export interface TripMapData {
  mappableEvents: TripEvent[]
  missingLocationEvents: TripEvent[]
  markers: TripMapMarker[]
  polyline: TripMapPolyline[]
  includePoints: TripMapPoint[]
  center: TripMapPoint
}

const DEFAULT_CENTER: TripMapPoint = {
  latitude: 30.27415,
  longitude: 120.15515,
}

const isFiniteCoordinate = (value: unknown): value is number => (
  typeof value === 'number' && Number.isFinite(value)
)

export const hasEventCoordinates = (event: Pick<TripEvent, 'latitude' | 'longitude'>) => (
  isFiniteCoordinate(event.latitude) && isFiniteCoordinate(event.longitude)
)

export const sortTripEventsForMap = (events: TripEvent[]) => (
  [...events].sort((a, b) => (
    new Date(a.startAt).getTime() - new Date(b.startAt).getTime()
    || a.sortOrder - b.sortOrder
    || a.title.localeCompare(b.title)
  ))
)

const eventLocationLabel = (event: TripEvent) => (
  event.locationName || event.title
)

export const buildTripMapData = (events: TripEvent[]): TripMapData => {
  const sorted = sortTripEventsForMap(events)
  const mappableEvents = sorted.filter(hasEventCoordinates)
  const missingLocationEvents = sorted.filter((event) => !hasEventCoordinates(event))
  const includePoints = mappableEvents.map((event) => ({
    latitude: event.latitude as number,
    longitude: event.longitude as number,
  }))
  const markers = mappableEvents.map((event, index) => ({
    id: index + 1,
    latitude: event.latitude as number,
    longitude: event.longitude as number,
    title: eventLocationLabel(event),
    callout: {
      content: `${index + 1}. ${eventLocationLabel(event)}`,
      color: '#281330',
      fontSize: 12,
      borderRadius: 8,
      bgColor: '#ffffff',
      padding: 8,
      display: 'ALWAYS' as const,
    },
  }))

  return {
    mappableEvents,
    missingLocationEvents,
    markers,
    polyline: includePoints.length >= 2
      ? [{
          points: includePoints,
          color: '#e040a0',
          width: 5,
          dottedLine: false,
          arrowLine: true,
        }]
      : [],
    includePoints,
    center: includePoints[0] || DEFAULT_CENTER,
  }
}
```

- [ ] **Step 4: Run frontend type check and confirm helper compiles**

Run:

```bash
cd miniapp && npm run type-check
```

Expected: type check passes after the helper and type updates.

- [ ] **Step 5: Commit frontend types and helper**

```bash
git add miniapp/src/services/trip-event.ts miniapp/src/services/ai-import.ts miniapp/src/utils/trip-map.ts
git commit -m "feat: add trip map data helper"
```

---

### Task 4: Trip Edit Page Map UI and Location Picker

**Files:**
- Modify: `miniapp/src/pages/edit/index.vue`

- [ ] **Step 1: Import map helper**

In `miniapp/src/pages/edit/index.vue`, add this import with the service imports:

```ts
import { buildTripMapData, hasEventCoordinates } from '../../utils/trip-map'
```

- [ ] **Step 2: Add tab state and event form coordinate state**

Add after `const tripEvents = ref<TripEvent[]>([])`:

```ts
const activeTripView = ref<'schedule' | 'map' | 'checklist'>('schedule')
```

Extend `EventFormState` with:

```ts
  address: string
  latitude: number | null
  longitude: number | null
```

Extend the `eventForm` initial state with:

```ts
  address: '',
  latitude: null,
  longitude: null,
```

Add computed map data after `eventGroups`:

```ts
const tripMapData = computed(() => buildTripMapData(tripEvents.value))

const eventLocationStatusLabel = computed(() => (
  eventForm.latitude !== null && eventForm.longitude !== null
    ? `已绑定地图位置${eventForm.address ? `：${eventForm.address}` : ''}`
    : '未绑定地图位置'
))
```

- [ ] **Step 3: Reset and hydrate coordinate state**

In `resetEventForm`, add:

```ts
  eventForm.address = ''
  eventForm.latitude = null
  eventForm.longitude = null
```

In `onEditAiCandidate`, add after `eventForm.locationName = candidate.locationName || ''`:

```ts
  eventForm.address = candidate.address || ''
  eventForm.latitude = candidate.latitude
  eventForm.longitude = candidate.longitude
```

In `onEditEvent`, add after `eventForm.locationName = event.locationName || ''`:

```ts
  eventForm.address = event.address || ''
  eventForm.latitude = event.latitude
  eventForm.longitude = event.longitude
```

- [ ] **Step 4: Add `uni.chooseLocation` handler**

Add this function near the event form handlers:

```ts
const onChooseEventLocation = () => {
  uni.chooseLocation({
    latitude: eventForm.latitude ?? undefined,
    longitude: eventForm.longitude ?? undefined,
    success: (res) => {
      eventForm.locationName = res.name || eventForm.locationName
      eventForm.address = res.address || eventForm.address
      eventForm.latitude = Number(res.latitude)
      eventForm.longitude = Number(res.longitude)
    },
    fail: (err) => {
      if (String(err.errMsg || '').includes('cancel')) return
      uni.showToast({ title: '暂时无法打开地图选择', icon: 'none' })
    },
  })
}
```

- [ ] **Step 5: Carry coordinates through candidate updates**

In `updateAiCandidateFromEventForm`, add these fields to the returned candidate object after `locationName`:

```ts
      address: eventForm.address.trim() || null,
      latitude: eventForm.latitude,
      longitude: eventForm.longitude,
```

- [ ] **Step 6: Carry coordinates through create and patch payloads**

In the `tripEventApi.patch` payload inside `onEventAddSubmit`, add after `locationName`:

```ts
        address: eventForm.address.trim() || null,
        latitude: eventForm.latitude,
        longitude: eventForm.longitude,
```

In the `tripEventApi.create` payload inside `onEventAddSubmit`, add after `locationName`:

```ts
      address: eventForm.address.trim() || null,
      latitude: eventForm.latitude,
      longitude: eventForm.longitude,
```

- [ ] **Step 7: Add the trip view tab template**

Add this block after the departure time row and before the current daily itinerary section:

```vue
    <view v-if="tripId" class="trip-view-tabs">
      <view
        class="trip-view-tab"
        :class="{ 'trip-view-tab--active': activeTripView === 'schedule' }"
        @click="activeTripView = 'schedule'"
      >
        <text>日程</text>
      </view>
      <view
        class="trip-view-tab"
        :class="{ 'trip-view-tab--active': activeTripView === 'map' }"
        @click="activeTripView = 'map'"
      >
        <text>地图</text>
      </view>
      <view
        class="trip-view-tab"
        :class="{ 'trip-view-tab--active': activeTripView === 'checklist' }"
        @click="activeTripView = 'checklist'"
      >
        <text>清单</text>
      </view>
    </view>
```

- [ ] **Step 8: Wrap schedule and checklist sections by active tab**

Change the root `<view>` immediately below `<!-- 每日行程 -->` from:

```vue
    <view class="section">
```

to:

```vue
    <view v-if="!tripId || activeTripView === 'schedule'" class="section">
```

Change the root `<view>` immediately below `<!-- 准备好了吗？检查清单 -->` from:

```vue
    <view class="section">
```

to:

```vue
    <view v-if="!tripId || activeTripView === 'checklist'" class="section">
```

- [ ] **Step 9: Add map section template**

Insert this block between the daily itinerary section and checklist section:

```vue
    <view v-if="tripId && activeTripView === 'map'" class="section">
      <view class="section-head">
        <view class="section-icon">
          <CandyIcon name="pin" />
        </view>
        <text class="section-title">路线地图</text>
      </view>
      <view class="candy-card map-panel">
        <map
          v-if="tripMapData.mappableEvents.length"
          class="route-map"
          :latitude="tripMapData.center.latitude"
          :longitude="tripMapData.center.longitude"
          :markers="tripMapData.markers"
          :polyline="tripMapData.polyline"
          :include-points="tripMapData.includePoints"
          :show-location="false"
        />
        <view v-else class="empty-events map-empty">
          <text class="empty-events__title">还没有可上地图的地点</text>
          <text class="empty-events__hint">添加事件后，用地图选择地点即可生成路线</text>
        </view>

        <view v-if="tripMapData.mappableEvents.length" class="map-route-list">
          <view
            v-for="(event, index) in tripMapData.mappableEvents"
            :key="event.id"
            class="map-route-row"
          >
            <text class="map-route-index">{{ index + 1 }}</text>
            <view class="map-route-copy">
              <text class="map-route-title">{{ event.locationName || event.title }}</text>
              <text class="map-route-meta">{{ eventTimeRange(event) }} · {{ event.title }}</text>
            </view>
          </view>
        </view>

        <view v-if="tripMapData.missingLocationEvents.length" class="map-missing">
          <text class="map-missing__title">未上地图</text>
          <view
            v-for="event in tripMapData.missingLocationEvents"
            :key="event.id"
            class="map-missing-row"
          >
            <view class="map-missing-copy">
              <text class="map-missing-title">{{ event.locationName || event.title }}</text>
              <text class="map-missing-meta">{{ eventTimeRange(event) }} · 未选择地图地点</text>
            </view>
            <button class="mini-action mini-action--secondary" @click="onEditEvent(event)">
              选择地点
            </button>
          </view>
        </view>
      </view>
    </view>
```

- [ ] **Step 10: Replace location input in event modal**

Replace the existing single location `<input class="candy-input modal-input" ... />` with:

```vue
            <view class="event-location-block">
              <text class="modal-field-label">地点</text>
              <view class="event-location-row">
                <input
                  class="candy-input modal-input event-location-input"
                  v-model="eventForm.locationName"
                  placeholder="地点，例如：东京国立博物馆"
                />
                <button class="mini-action mini-action--secondary event-location-button" @click="onChooseEventLocation">
                  地图选择
                </button>
              </view>
              <text class="event-location-status" :class="{ 'event-location-status--bound': hasEventCoordinates(eventForm) }">
                {{ eventLocationStatusLabel }}
              </text>
            </view>
```

- [ ] **Step 11: Add styles**

Add these styles before the modal styles:

```scss
.trip-view-tabs {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10rpx;
  padding: 10rpx;
  border-radius: $candy-radius-full;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: $candy-shadow-card;
}
.trip-view-tab {
  min-width: 0;
  height: 64rpx;
  border-radius: $candy-radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  color: $candy-on-surface-variant;
  font-size: $candy-font-label-md;
  font-weight: 800;
}
.trip-view-tab--active {
  background: $candy-primary;
  color: $candy-on-primary;
  box-shadow: 0 8rpx 22rpx rgba(224, 64, 160, 0.18);
}
.map-panel {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  padding: 18rpx;
}
.route-map {
  width: 100%;
  height: 520rpx;
  border-radius: $candy-radius-md;
  overflow: hidden;
}
.map-empty {
  min-height: 360rpx;
}
.map-route-list,
.map-missing {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}
.map-route-row,
.map-missing-row {
  min-width: 0;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 14rpx;
  padding: 14rpx;
  border-radius: $candy-radius-md;
  background: $candy-surface-container-lowest;
}
.map-route-index {
  flex: 0 0 46rpx;
  width: 46rpx;
  height: 46rpx;
  line-height: 46rpx;
  border-radius: 50%;
  text-align: center;
  background: $candy-primary;
  color: $candy-on-primary;
  font-size: 22rpx;
  font-weight: 900;
}
.map-route-copy,
.map-missing-copy {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}
.map-route-title,
.map-missing-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: $candy-on-surface;
  font-size: $candy-font-body-md;
  font-weight: 800;
}
.map-route-meta,
.map-missing-meta,
.event-location-status {
  color: $candy-on-surface-variant;
  font-size: $candy-font-label-md;
}
.map-missing__title {
  color: $candy-on-surface;
  font-size: $candy-font-body-md;
  font-weight: 800;
}
.event-location-block {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}
.event-location-row {
  min-width: 0;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12rpx;
}
.event-location-input {
  flex: 1;
}
.event-location-button {
  flex: 0 0 156rpx;
}
.event-location-status--bound {
  color: $candy-primary;
  font-weight: 700;
}
```

- [ ] **Step 12: Run frontend type check**

Run:

```bash
cd miniapp && npm run type-check
```

Expected: type check passes.

- [ ] **Step 13: Run miniapp build**

Run:

```bash
cd miniapp && npm run build:mp-weixin
```

Expected: build exits 0 and prints `DONE  Build complete.`

- [ ] **Step 14: Commit frontend UI**

```bash
git add miniapp/src/pages/edit/index.vue
git commit -m "feat: add trip map view"
```

---

### Task 5: Full Verification

**Files:**
- Verify all modified files from Tasks 1 to 4.

- [ ] **Step 1: Run backend tests**

Run:

```bash
cd backend && uv run pytest tests -q
```

Expected: all backend tests pass.

- [ ] **Step 2: Run backend lint**

Run:

```bash
cd backend && uv run ruff check app tests
```

Expected: no lint errors.

- [ ] **Step 3: Run frontend type check**

Run:

```bash
cd miniapp && npm run type-check
```

Expected: type check passes.

- [ ] **Step 4: Run miniapp production build**

Run:

```bash
cd miniapp && npm run build:mp-weixin
```

Expected: build exits 0 and prints `DONE  Build complete.`

- [ ] **Step 5: Check final git status**

Run:

```bash
git status --short
```

Expected: empty output after all planned commits.
