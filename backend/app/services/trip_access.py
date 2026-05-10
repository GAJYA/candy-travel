from uuid import UUID

from sqlalchemy import Select, exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Trip, TripMember


def accessible_trip_filter(user_id: UUID):
    member_exists = exists(
        select(TripMember.id).where(
            TripMember.trip_id == Trip.id,
            TripMember.user_id == user_id,
        )
    )
    return or_(Trip.user_id == user_id, member_exists)


def select_accessible_trip(user_id: UUID, trip_id: UUID) -> Select[tuple[Trip]]:
    return select(Trip).where(
        Trip.id == trip_id,
        Trip.deleted_at.is_(None),
        accessible_trip_filter(user_id),
    )


async def get_accessible_trip(
    session: AsyncSession, *, user_id: UUID, trip_id: UUID
) -> Trip | None:
    return await session.scalar(select_accessible_trip(user_id, trip_id))


async def is_trip_accessible(
    session: AsyncSession, *, user_id: UUID, trip_id: UUID
) -> bool:
    trip_id_result = await session.scalar(
        select(Trip.id).where(
            Trip.id == trip_id,
            Trip.deleted_at.is_(None),
            accessible_trip_filter(user_id),
        )
    )
    return trip_id_result is not None
