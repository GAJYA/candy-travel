from datetime import UTC, datetime, timedelta
from secrets import choice
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import CurrentUser, SessionDep
from app.models import Trip, TripInvite, TripMember, User
from app.schemas.trip_invite import (
    TripInviteAcceptIn,
    TripInviteAcceptOut,
    TripInviteCreateOut,
    TripInvitePreviewOut,
    TripInviteStatus,
)
from app.schemas.trip_member import TripMemberOut
from app.services.trip_access import get_accessible_trip

router = APIRouter(tags=["trip-invites"])

INVITE_EXPIRE_DAYS = 7
INVITE_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _new_invite_code() -> str:
    return "".join(choice(INVITE_CODE_ALPHABET) for _ in range(6))


def _invite_status(invite: TripInvite, now: datetime) -> TripInviteStatus:
    if invite.accepted_by_user_id is not None:
        return TripInviteStatus.accepted
    if invite.expires_at <= now:
        return TripInviteStatus.expired
    return TripInviteStatus.active


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


async def _get_invite_context(session: AsyncSession, token: str):
    row = (
        await session.execute(
            select(TripInvite, Trip, User)
            .join(Trip, Trip.id == TripInvite.trip_id)
            .join(User, User.id == TripInvite.inviter_user_id)
            .where(TripInvite.token == token, Trip.deleted_at.is_(None))
        )
    ).one_or_none()
    return row if row is None else (row[0], row[1], row[2])


@router.post(
    "/trips/{trip_id}/invite",
    response_model=TripInviteCreateOut,
    response_model_by_alias=True,
    status_code=201,
)
async def create_trip_invite(
    trip_id: UUID,
    user: CurrentUser,
    session: SessionDep,
) -> TripInviteCreateOut:
    trip = await get_accessible_trip(session, user_id=user.id, trip_id=trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="trip not found")

    now = datetime.now(UTC)
    for _ in range(3):
        code = _new_invite_code()
        invite = TripInvite(
            trip_id=trip.id,
            inviter_user_id=user.id,
            token=code,
            expires_at=now + timedelta(days=INVITE_EXPIRE_DAYS),
        )
        session.add(invite)
        try:
            await session.commit()
            return TripInviteCreateOut(
                trip_id=trip.id,
                code=code,
                expires_at=invite.expires_at,
            )
        except IntegrityError:
            await session.rollback()

    raise HTTPException(status_code=500, detail="failed to create invite")


@router.post(
    "/trip-invites/accept",
    response_model=TripInviteAcceptOut,
    response_model_by_alias=True,
)
async def accept_trip_invite_by_code(
    payload: TripInviteAcceptIn,
    user: CurrentUser,
    session: SessionDep,
) -> TripInviteAcceptOut:
    return await _accept_trip_invite(payload.code, user=user, session=session)


@router.get(
    "/trip-invites/{token}",
    response_model=TripInvitePreviewOut,
    response_model_by_alias=True,
)
async def preview_trip_invite(token: str, session: SessionDep) -> TripInvitePreviewOut:
    context = await _get_invite_context(session, token.strip().upper())
    if context is None:
        raise HTTPException(status_code=404, detail="invite not found")

    invite, trip, inviter = context
    return TripInvitePreviewOut(
        trip_id=trip.id,
        trip_title=trip.title,
        inviter_nickname=inviter.nickname,
        status=_invite_status(invite, datetime.now(UTC)),
        expires_at=invite.expires_at,
    )


@router.post(
    "/trip-invites/{token}/accept",
    response_model=TripInviteAcceptOut,
    response_model_by_alias=True,
)
async def accept_trip_invite(
    token: str,
    user: CurrentUser,
    session: SessionDep,
) -> TripInviteAcceptOut:
    return await _accept_trip_invite(token, user=user, session=session)


async def _accept_trip_invite(
    code: str,
    user: CurrentUser,
    session: AsyncSession,
) -> TripInviteAcceptOut:
    context = await _get_invite_context(session, code.strip().upper())
    if context is None:
        raise HTTPException(status_code=404, detail="invite not found")

    invite, trip, _inviter = context
    now = datetime.now(UTC)
    if invite.expires_at <= now:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="invite expired")

    existing = await _get_existing_member(session, trip_id=trip.id, user_id=user.id)
    if existing is not None:
        return TripInviteAcceptOut(trip_id=trip.id, member=_member_out(*existing))

    if invite.accepted_by_user_id is not None:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="invite already accepted",
        )

    member = TripMember(trip_id=trip.id, user_id=user.id, role="editor")
    invite.accepted_by_user_id = user.id
    invite.accepted_at = now
    session.add(member)
    await session.commit()
    await session.refresh(member)

    return TripInviteAcceptOut(
        trip_id=trip.id,
        member=_member_out(member, user),
    )
