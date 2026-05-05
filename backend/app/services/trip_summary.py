"""摘要派生 + 摘要级 PATCH 应用逻辑"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Trip, TripEvent
from app.schemas.trip_event import TransportMode
from app.schemas.trip_summary import (
    TripStayPatch,
    TripStaySummary,
    TripSummaryOut,
    TripSummaryPatchIn,
    TripTransportPatch,
    TripTransportSummary,
)


async def _first_event(
    session: AsyncSession, trip_id: UUID, event_type: str
) -> TripEvent | None:
    return await session.scalar(
        select(TripEvent)
        .where(
            TripEvent.trip_id == trip_id,
            TripEvent.event_type == event_type,
            TripEvent.deleted_at.is_(None),
        )
        .order_by(TripEvent.start_at, TripEvent.sort_order)
        .limit(1)
    )


def _transport_summary_from_event(event: TripEvent) -> TripTransportSummary:
    meta = event.meta or {}
    raw_mode = meta.get("mode")
    mode = TransportMode(raw_mode) if raw_mode in TransportMode._value2member_map_ else None
    return TripTransportSummary(
        event_id=event.id,
        mode=mode,
        depart_at=event.start_at,
        arrive_at=event.end_at,
        from_city=meta.get("fromCity"),
        to_city=meta.get("toCity"),
        flight_no=meta.get("flightNo"),
        train_no=meta.get("trainNo"),
        seat=meta.get("seat"),
        ref_code=meta.get("refCode"),
    )


def _stay_summary_from_event(event: TripEvent) -> TripStaySummary:
    meta = event.meta or {}
    return TripStaySummary(
        event_id=event.id,
        hotel_name=meta.get("hotelName") or event.title,
        checkin_at=event.start_at,
        checkout_at=event.end_at,
        address=event.address,
        room_type=meta.get("roomType"),
        ref_code=meta.get("refCode"),
        guests=meta.get("guests"),
    )


async def derive_summary(session: AsyncSession, trip_id: UUID) -> TripSummaryOut:
    """从 events 表派生 trip 的 transport / stay 摘要"""
    transport = await _first_event(session, trip_id, "transport")
    stay = await _first_event(session, trip_id, "stay")
    return TripSummaryOut(
        transport=_transport_summary_from_event(transport) if transport else None,
        stay=_stay_summary_from_event(stay) if stay else None,
    )


# --- PATCH 应用 ---


def _apply_transport_patch(event: TripEvent, payload: TripTransportPatch) -> None:
    """upsert 一条已有 transport event 的字段。"""
    field_set = payload.model_fields_set
    if "depart_at" in field_set and payload.depart_at is not None:
        event.start_at = payload.depart_at
    if "arrive_at" in field_set:
        event.end_at = payload.arrive_at

    meta = dict(event.meta or {})
    if "mode" in field_set and payload.mode is not None:
        meta["mode"] = payload.mode.value
    if "from_city" in field_set:
        meta["fromCity"] = payload.from_city
    if "to_city" in field_set:
        meta["toCity"] = payload.to_city
    if "flight_no" in field_set:
        meta["flightNo"] = payload.flight_no
    if "train_no" in field_set:
        meta["trainNo"] = payload.train_no
    if "seat" in field_set:
        meta["seat"] = payload.seat
    if "ref_code" in field_set:
        meta["refCode"] = payload.ref_code
    event.meta = meta

    # title 自动跟随 mode（如果用户没自定义过）
    if "mode" in field_set and payload.mode is not None:
        mode_label = {
            "flight": "飞机",
            "train": "火车",
            "bus": "巴士",
            "car": "自驾",
        }.get(payload.mode.value, "出行")
        event.title = f"{mode_label}"


def _build_transport_event(
    user_id: UUID, trip: Trip, payload: TripTransportPatch
) -> TripEvent:
    meta: dict[str, object] = {}
    if payload.mode is not None:
        meta["mode"] = payload.mode.value
    for src, key in (
        (payload.from_city, "fromCity"),
        (payload.to_city, "toCity"),
        (payload.flight_no, "flightNo"),
        (payload.train_no, "trainNo"),
        (payload.seat, "seat"),
        (payload.ref_code, "refCode"),
    ):
        if src is not None:
            meta[key] = src

    title = "出行"
    if payload.mode is not None:
        title = {
            "flight": "飞机",
            "train": "火车",
            "bus": "巴士",
            "car": "自驾",
        }.get(payload.mode.value, "出行")

    # start_at 是 NOT NULL，必须给默认值。
    start_at = payload.depart_at or datetime.now(UTC)
    return TripEvent(
        user_id=user_id,
        trip_id=trip.id,
        event_type="transport",
        title=title,
        start_at=start_at,
        end_at=payload.arrive_at,
        meta=meta,
        status="confirmed",
        source="manual",
    )


def _apply_stay_patch(event: TripEvent, payload: TripStayPatch) -> None:
    field_set = payload.model_fields_set
    if "checkin_at" in field_set and payload.checkin_at is not None:
        event.start_at = payload.checkin_at
    if "checkout_at" in field_set:
        event.end_at = payload.checkout_at
    if "address" in field_set:
        event.address = payload.address
    if "hotel_name" in field_set and payload.hotel_name is not None:
        event.title = payload.hotel_name

    meta = dict(event.meta or {})
    if "hotel_name" in field_set:
        meta["hotelName"] = payload.hotel_name
    if "room_type" in field_set:
        meta["roomType"] = payload.room_type
    if "ref_code" in field_set:
        meta["refCode"] = payload.ref_code
    if "guests" in field_set:
        meta["guests"] = payload.guests
    event.meta = meta


def _build_stay_event(
    user_id: UUID, trip: Trip, payload: TripStayPatch
) -> TripEvent:
    meta: dict[str, object] = {}
    for src, key in (
        (payload.hotel_name, "hotelName"),
        (payload.room_type, "roomType"),
        (payload.ref_code, "refCode"),
        (payload.guests, "guests"),
    ):
        if src is not None:
            meta[key] = src

    title = payload.hotel_name or "酒店"
    start_at = payload.checkin_at or datetime.now(UTC)
    return TripEvent(
        user_id=user_id,
        trip_id=trip.id,
        event_type="stay",
        title=title,
        start_at=start_at,
        end_at=payload.checkout_at,
        address=payload.address,
        meta=meta,
        status="confirmed",
        source="manual",
    )


async def apply_summary_patch(
    session: AsyncSession, *, trip: Trip, payload: TripSummaryPatchIn, user_id: UUID
) -> None:
    """根据 payload 更新 trip 顶级字段 + transport / stay 段。

    transport / stay 段语义：
      - 字段未传     → 不动现有 event
      - 字段为 None  → 软删现有 event
      - 字段为 obj   → upsert（已有则 patch；没有则 insert）
    """
    # ---- trip 顶级字段 ----
    field_set = payload.model_fields_set
    if "title" in field_set and payload.title is not None:
        trip.title = payload.title
    if "destination_city" in field_set:
        trip.destination_city = payload.destination_city
    if "note" in field_set:
        trip.note = payload.note
    if "status" in field_set and payload.status is not None:
        trip.status = payload.status.value
    if "start_date" in field_set:
        trip.start_date = payload.start_date
    if "end_date" in field_set:
        trip.end_date = payload.end_date
    if "timezone" in field_set and payload.timezone is not None:
        trip.timezone = payload.timezone

    if (
        trip.start_date
        and trip.end_date
        and trip.start_date > trip.end_date
    ):
        raise ValueError("start_date must be <= end_date")

    # ---- transport 段 ----
    if "transport" in field_set:
        existing = await _first_event(session, trip.id, "transport")
        if payload.transport is None:
            if existing:
                existing.deleted_at = datetime.now(UTC)
        else:
            if existing:
                _apply_transport_patch(existing, payload.transport)
            else:
                session.add(_build_transport_event(user_id, trip, payload.transport))

    # ---- stay 段 ----
    if "stay" in field_set:
        existing = await _first_event(session, trip.id, "stay")
        if payload.stay is None:
            if existing:
                existing.deleted_at = datetime.now(UTC)
        else:
            if existing:
                _apply_stay_patch(existing, payload.stay)
            else:
                session.add(_build_stay_event(user_id, trip, payload.stay))
