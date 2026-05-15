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
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="image too large",
            )
        total += len(data)
        if total > max_total_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="images too large",
            )
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
            latitude=candidate.latitude,
            longitude=candidate.longitude,
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
