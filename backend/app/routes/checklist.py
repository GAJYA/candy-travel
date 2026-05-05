from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.deps import CurrentUser, SessionDep
from app.models import ChecklistItem, ChecklistTemplate, Trip
from app.schemas.checklist import (
    ChecklistItemCreate,
    ChecklistItemOut,
    ChecklistItemPatch,
    ChecklistTemplateOut,
)

router = APIRouter(tags=["checklist"])


async def _get_user_trip(session, user_id: UUID, trip_id: UUID) -> Trip | None:
    return await session.scalar(
        select(Trip).where(
            Trip.id == trip_id,
            Trip.user_id == user_id,
            Trip.deleted_at.is_(None),
        )
    )


async def _get_user_item(
    session, user_id: UUID, item_id: UUID
) -> ChecklistItem | None:
    return await session.scalar(
        select(ChecklistItem).where(
            ChecklistItem.id == item_id, ChecklistItem.user_id == user_id
        )
    )


# ---- 模板 ----


@router.get(
    "/checklist-templates",
    response_model=list[ChecklistTemplateOut],
    response_model_by_alias=True,
)
async def list_templates(
    user: CurrentUser, session: SessionDep
) -> list[ChecklistTemplateOut]:
    rows = await session.scalars(
        select(ChecklistTemplate).order_by(
            ChecklistTemplate.category, ChecklistTemplate.sort_order
        )
    )
    return [ChecklistTemplateOut.model_validate(t) for t in rows.all()]


# ---- trip 实例 ----


@router.get(
    "/trips/{trip_id}/checklist-items",
    response_model=list[ChecklistItemOut],
    response_model_by_alias=True,
)
async def list_items(
    trip_id: UUID, user: CurrentUser, session: SessionDep
) -> list[ChecklistItemOut]:
    trip = await _get_user_trip(session, user.id, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="trip not found")
    rows = await session.scalars(
        select(ChecklistItem)
        .where(ChecklistItem.trip_id == trip.id)
        .order_by(ChecklistItem.category, ChecklistItem.sort_order)
    )
    return [ChecklistItemOut.model_validate(i) for i in rows.all()]


@router.post(
    "/trips/{trip_id}/checklist-items",
    response_model=ChecklistItemOut,
    response_model_by_alias=True,
    status_code=201,
)
async def create_item(
    trip_id: UUID,
    payload: ChecklistItemCreate,
    user: CurrentUser,
    session: SessionDep,
) -> ChecklistItemOut:
    trip = await _get_user_trip(session, user.id, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="trip not found")

    source = "template" if payload.template_id else "manual"
    item = ChecklistItem(
        user_id=user.id,
        trip_id=trip.id,
        label=payload.label,
        category=payload.category.value,
        sort_order=payload.sort_order,
        source=source,
        template_id=payload.template_id,
        checked=payload.checked,
    )
    session.add(item)
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail="label already exists in this trip") from e
    await session.refresh(item)
    return ChecklistItemOut.model_validate(item)


@router.patch(
    "/checklist-items/{item_id}",
    response_model=ChecklistItemOut,
    response_model_by_alias=True,
)
async def patch_item(
    item_id: UUID,
    payload: ChecklistItemPatch,
    user: CurrentUser,
    session: SessionDep,
) -> ChecklistItemOut:
    item = await _get_user_item(session, user.id, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if key == "category" and value is not None:
            value = value.value if hasattr(value, "value") else value
        setattr(item, key, value)

    if updates:
        item.updated_at = datetime.now(UTC)
        try:
            await session.commit()
        except IntegrityError as e:
            await session.rollback()
            raise HTTPException(
                status_code=400, detail="label already exists in this trip"
            ) from e
        await session.refresh(item)
    return ChecklistItemOut.model_validate(item)


@router.delete("/checklist-items/{item_id}", status_code=204)
async def delete_item(
    item_id: UUID, user: CurrentUser, session: SessionDep
) -> Response:
    item = await _get_user_item(session, user.id, item_id)
    if item is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    await session.delete(item)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
