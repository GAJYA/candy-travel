from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.deps import CurrentUser, SessionDep
from app.models import Trip
from app.schemas.trip import TripCreate, TripOut, TripPatch

router = APIRouter(prefix="/trips", tags=["trips"])


def _select_user_trip(user_id: UUID, trip_id: UUID):
    return select(Trip).where(
        Trip.id == trip_id,
        Trip.user_id == user_id,
        Trip.deleted_at.is_(None),
    )


@router.post("", response_model=TripOut, response_model_by_alias=True, status_code=201)
async def create_trip(
    payload: TripCreate, user: CurrentUser, session: SessionDep
) -> TripOut:
    trip = Trip(
        user_id=user.id,
        title=payload.title,
        destination_city=payload.destination_city,
        status=payload.status.value,
        start_date=payload.start_date,
        end_date=payload.end_date,
        cover_image_url=payload.cover_image_url,
        note=payload.note,
        timezone=payload.timezone,
    )
    session.add(trip)
    await session.commit()
    await session.refresh(trip)
    return TripOut.model_validate(trip)


@router.get("", response_model=list[TripOut], response_model_by_alias=True)
async def list_trips(user: CurrentUser, session: SessionDep) -> list[TripOut]:
    stmt = (
        select(Trip)
        .where(Trip.user_id == user.id, Trip.deleted_at.is_(None))
        .order_by(Trip.start_date.desc().nullslast(), Trip.created_at.desc())
    )
    result = await session.scalars(stmt)
    return [TripOut.model_validate(t) for t in result.all()]


@router.get("/{trip_id}", response_model=TripOut, response_model_by_alias=True)
async def get_trip(trip_id: UUID, user: CurrentUser, session: SessionDep) -> TripOut:
    trip = await session.scalar(_select_user_trip(user.id, trip_id))
    if trip is None:
        raise HTTPException(status_code=404, detail="trip not found")
    return TripOut.model_validate(trip)


@router.patch("/{trip_id}", response_model=TripOut, response_model_by_alias=True)
async def patch_trip(
    trip_id: UUID,
    payload: TripPatch,
    user: CurrentUser,
    session: SessionDep,
) -> TripOut:
    trip = await session.scalar(_select_user_trip(user.id, trip_id))
    if trip is None:
        raise HTTPException(status_code=404, detail="trip not found")

    updates = payload.model_dump(exclude_unset=True)
    if "status" in updates and updates["status"] is not None:
        # enum -> string for ORM column
        updates["status"] = updates["status"].value

    for key, value in updates.items():
        setattr(trip, key, value)

    # 合并后再校验日期区间
    start = trip.start_date
    end = trip.end_date
    if start and end and start > end:
        raise HTTPException(status_code=400, detail="start_date must be <= end_date")

    if updates:
        trip.updated_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(trip)
    return TripOut.model_validate(trip)


@router.delete("/{trip_id}", status_code=204)
async def delete_trip(
    trip_id: UUID, user: CurrentUser, session: SessionDep
) -> Response:
    trip = await session.scalar(
        select(Trip).where(Trip.id == trip_id, Trip.user_id == user.id)
    )
    if trip is None or trip.deleted_at is not None:
        # 幂等：不存在 / 已删，都返回 204
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    trip.deleted_at = datetime.now(UTC)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
