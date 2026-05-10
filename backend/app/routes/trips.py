from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import CurrentUser, SessionDep
from app.models import Trip, TripMember, User
from app.schemas.trip import TripCreate, TripOut, TripPatch
from app.schemas.trip_member import TripMemberAddIn, TripMemberOut
from app.schemas.trip_summary import (
    TripDetailOut,
    TripSummaryPatchIn,
)
from app.services.checklist_seed import copy_default_templates_to_trip
from app.services.trip_access import accessible_trip_filter, get_accessible_trip
from app.services.trip_summary import apply_summary_patch, derive_summary

router = APIRouter(prefix="/trips", tags=["trips"])


def _member_out(member: TripMember, member_user: User) -> TripMemberOut:
    return TripMemberOut.model_validate(
        {
            "id": member.id,
            "trip_id": member.trip_id,
            "role": member.role,
            "user": member_user,
            "created_at": member.created_at,
        }
    )


async def _get_existing_member(
    session: AsyncSession, *, trip_id: UUID, user_id: UUID
) -> tuple[TripMember, User] | None:
    row = (
        await session.execute(
            select(TripMember, User)
            .join(User, User.id == TripMember.user_id)
            .where(TripMember.trip_id == trip_id, TripMember.user_id == user_id)
        )
    ).one_or_none()
    return row if row is None else (row[0], row[1])


async def _resolve_member_user(session: AsyncSession, payload: TripMemberAddIn) -> User:
    if payload.user_id is not None:
        target = await session.scalar(
            select(User).where(User.id == payload.user_id, User.deleted_at.is_(None))
        )
        if target is None:
            raise HTTPException(status_code=404, detail="user not found")
        return target

    nickname = (payload.nickname or "").strip()
    rows = (
        await session.scalars(
            select(User).where(
                func.lower(User.nickname) == nickname.lower(),
                User.deleted_at.is_(None),
            )
        )
    ).all()
    if not rows:
        raise HTTPException(status_code=404, detail="user not found")
    if len(rows) > 1:
        raise HTTPException(status_code=400, detail="nickname is ambiguous")
    return rows[0]


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
    await session.flush()  # 需要 trip.id 来拷模板
    session.add(TripMember(trip_id=trip.id, user_id=user.id, role="owner"))
    await copy_default_templates_to_trip(session, user_id=user.id, trip_id=trip.id)
    await session.commit()
    await session.refresh(trip)
    return TripOut.model_validate(trip)


@router.get("", response_model=list[TripOut], response_model_by_alias=True)
async def list_trips(user: CurrentUser, session: SessionDep) -> list[TripOut]:
    stmt = (
        select(Trip)
        .where(Trip.deleted_at.is_(None), accessible_trip_filter(user.id))
        .order_by(Trip.start_date.desc().nullslast(), Trip.created_at.desc())
    )
    result = await session.scalars(stmt)
    return [TripOut.model_validate(t) for t in result.all()]


@router.get(
    "/{trip_id}",
    response_model=TripDetailOut,
    response_model_by_alias=True,
)
async def get_trip(
    trip_id: UUID, user: CurrentUser, session: SessionDep
) -> TripDetailOut:
    trip = await get_accessible_trip(session, user_id=user.id, trip_id=trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="trip not found")
    summary = await derive_summary(session, trip.id)
    base = TripOut.model_validate(trip).model_dump()
    return TripDetailOut(**base, summary=summary)


@router.patch(
    "/{trip_id}/summary",
    response_model=TripDetailOut,
    response_model_by_alias=True,
)
async def patch_trip_summary(
    trip_id: UUID,
    payload: TripSummaryPatchIn,
    user: CurrentUser,
    session: SessionDep,
) -> TripDetailOut:
    trip = await get_accessible_trip(session, user_id=user.id, trip_id=trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="trip not found")
    try:
        await apply_summary_patch(
            session, trip=trip, payload=payload, user_id=user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    trip.updated_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(trip)
    summary = await derive_summary(session, trip.id)
    base = TripOut.model_validate(trip).model_dump()
    return TripDetailOut(**base, summary=summary)


@router.patch("/{trip_id}", response_model=TripOut, response_model_by_alias=True)
async def patch_trip(
    trip_id: UUID,
    payload: TripPatch,
    user: CurrentUser,
    session: SessionDep,
) -> TripOut:
    trip = await get_accessible_trip(session, user_id=user.id, trip_id=trip_id)
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
    trip = await session.scalar(select(Trip).where(Trip.id == trip_id))
    if trip is None or trip.deleted_at is not None:
        # 幂等：不存在 / 已删，都返回 204
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    if trip.user_id != user.id:
        if await get_accessible_trip(session, user_id=user.id, trip_id=trip_id):
            raise HTTPException(status_code=403, detail="only trip owner can delete trip")
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    trip.deleted_at = datetime.now(UTC)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{trip_id}/members",
    response_model=list[TripMemberOut],
    response_model_by_alias=True,
)
async def list_members(
    trip_id: UUID, user: CurrentUser, session: SessionDep
) -> list[TripMemberOut]:
    trip = await get_accessible_trip(session, user_id=user.id, trip_id=trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="trip not found")

    rows = (
        await session.execute(
            select(TripMember, User)
            .join(User, User.id == TripMember.user_id)
            .where(TripMember.trip_id == trip.id)
            .order_by(TripMember.role.desc(), TripMember.created_at)
        )
    ).all()
    return [_member_out(member, member_user) for member, member_user in rows]


@router.post(
    "/{trip_id}/members",
    response_model=TripMemberOut,
    response_model_by_alias=True,
    status_code=201,
)
async def add_member(
    trip_id: UUID,
    payload: TripMemberAddIn,
    user: CurrentUser,
    session: SessionDep,
    response: Response,
) -> TripMemberOut:
    trip = await get_accessible_trip(session, user_id=user.id, trip_id=trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="trip not found")

    target = await _resolve_member_user(session, payload)
    existing = await _get_existing_member(session, trip_id=trip.id, user_id=target.id)
    if existing is not None:
        response.status_code = status.HTTP_200_OK
        return _member_out(*existing)

    member = TripMember(trip_id=trip.id, user_id=target.id, role="editor")
    session.add(member)
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        existing = await _get_existing_member(session, trip_id=trip.id, user_id=target.id)
        if existing is None:
            raise HTTPException(status_code=400, detail="member already exists") from e
        response.status_code = status.HTTP_200_OK
        return _member_out(*existing)

    await session.refresh(member)
    return _member_out(member, target)
