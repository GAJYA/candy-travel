from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.deps import CurrentUser, SessionDep
from app.models import Trip, TripEvent
from app.schemas.trip_event import TripEventCreate, TripEventOut, TripEventPatch
from app.services.trip_access import accessible_trip_filter, get_accessible_trip

router = APIRouter(tags=["events"])


async def _get_user_trip(session, user_id: UUID, trip_id: UUID) -> Trip | None:
    return await get_accessible_trip(session, user_id=user_id, trip_id=trip_id)


async def _get_user_event(session, user_id: UUID, event_id: UUID) -> TripEvent | None:
    return await session.scalar(
        select(TripEvent)
        .join(Trip, Trip.id == TripEvent.trip_id)
        .where(
            TripEvent.id == event_id,
            TripEvent.deleted_at.is_(None),
            Trip.deleted_at.is_(None),
            accessible_trip_filter(user_id),
        )
    )


@router.get(
    "/trips/{trip_id}/events",
    response_model=list[TripEventOut],
    response_model_by_alias=True,
)
async def list_events(
    trip_id: UUID, user: CurrentUser, session: SessionDep
) -> list[TripEventOut]:
    trip = await _get_user_trip(session, user.id, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="trip not found")
    stmt = (
        select(TripEvent)
        .where(
            TripEvent.trip_id == trip.id,
            TripEvent.deleted_at.is_(None),
        )
        .order_by(TripEvent.start_at, TripEvent.sort_order)
    )
    rows = await session.scalars(stmt)
    return [TripEventOut.model_validate(e) for e in rows.all()]


@router.post(
    "/trips/{trip_id}/events",
    response_model=TripEventOut,
    response_model_by_alias=True,
    status_code=201,
)
async def create_event(
    trip_id: UUID,
    payload: TripEventCreate,
    user: CurrentUser,
    session: SessionDep,
) -> TripEventOut:
    trip = await _get_user_trip(session, user.id, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="trip not found")
    event = TripEvent(
        user_id=user.id,
        trip_id=trip.id,
        event_type=payload.event_type.value,
        title=payload.title,
        start_at=payload.start_at,
        end_at=payload.end_at,
        location_name=payload.location_name,
        address=payload.address,
        note=payload.note,
        meta=payload.meta or {},
        status=payload.status.value,
        source="manual",
        sort_order=payload.sort_order,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return TripEventOut.model_validate(event)


@router.patch(
    "/events/{event_id}",
    response_model=TripEventOut,
    response_model_by_alias=True,
)
async def patch_event(
    event_id: UUID,
    payload: TripEventPatch,
    user: CurrentUser,
    session: SessionDep,
) -> TripEventOut:
    event = await _get_user_event(session, user.id, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="event not found")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if key == "status" and value is not None:
            value = value.value if hasattr(value, "value") else value
        setattr(event, key, value)

    if event.end_at is not None and event.end_at < event.start_at:
        raise HTTPException(status_code=400, detail="end_at must be >= start_at")

    if updates:
        event.updated_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(event)
    return TripEventOut.model_validate(event)


@router.delete("/events/{event_id}", status_code=204)
async def delete_event(
    event_id: UUID, user: CurrentUser, session: SessionDep
) -> Response:
    event = await session.scalar(
        select(TripEvent)
        .join(Trip, Trip.id == TripEvent.trip_id)
        .where(
            TripEvent.id == event_id,
            Trip.deleted_at.is_(None),
            accessible_trip_filter(user.id),
        )
    )
    if event is None or event.deleted_at is not None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    event.deleted_at = datetime.now(UTC)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
