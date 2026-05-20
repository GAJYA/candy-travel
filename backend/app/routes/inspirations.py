import json
import re
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import ValidationError
from sqlalchemy import select

from app.deps import CurrentUser, SessionDep
from app.models import TravelInspiration
from app.schemas.ai_import import AiTripEventCandidate
from app.schemas.inspiration import (
    InspirationCreate,
    InspirationFromShareIn,
    InspirationOut,
    InspirationPatch,
    InspirationShareDraftOut,
)
from app.services.ai_client import AiClient, AiClientError
from app.services.xiaohongshu_client import (
    XiaohongshuClient,
    XiaohongshuClientError,
    extract_share_url,
    is_xiaohongshu_url,
)

router = APIRouter(prefix="/inspirations", tags=["inspirations"])

_EVENT_TYPES = {"transport", "stay", "activity", "reminder"}
_CONFIDENCES = {"high", "medium", "low"}
_EVENT_ICON_BY_TYPE = {
    "transport": "plane",
    "stay": "hotel",
    "activity": "pin",
    "reminder": "clock",
}


async def _read_shared_content(shared_text: str) -> tuple[str, str | None]:
    source_url = extract_share_url(shared_text)
    if not source_url:
        return shared_text, None

    if not is_xiaohongshu_url(source_url):
        return shared_text, source_url

    client = XiaohongshuClient()
    try:
        note = await client.read_shared_note(shared_text)
    except XiaohongshuClientError:
        return shared_text, source_url
    finally:
        await client.aclose()

    return f"{shared_text}\n\n小红书内容：\n{note.to_prompt_text()}", note.final_url


def _string_or_none(value: object, max_length: int | None = None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text[:max_length] if max_length else text


def _event_candidate_from_ai(raw: object, index: int) -> AiTripEventCandidate | None:
    if not isinstance(raw, dict):
        return None

    location_name = _string_or_none(
        raw.get("locationName")
        or raw.get("location_name")
        or raw.get("place")
        or raw.get("location"),
        128,
    )
    title = _string_or_none(raw.get("title"), 128) or location_name
    if not title:
        return None

    event_type = str(raw.get("eventType") or raw.get("event_type") or "activity").strip()
    if event_type not in _EVENT_TYPES:
        event_type = "activity"

    confidence = str(raw.get("confidence") or "medium").strip()
    if confidence not in _CONFIDENCES:
        confidence = "medium"

    warnings = raw.get("warnings")
    if not isinstance(warnings, list):
        warnings = []

    meta = raw.get("meta")
    if not isinstance(meta, dict):
        meta = {}
    else:
        meta = {str(key): value for key, value in meta.items()}
    if "dayOffset" not in meta and "dayOffset" in raw:
        meta["dayOffset"] = raw.get("dayOffset")
    meta.setdefault("icon", _EVENT_ICON_BY_TYPE[event_type])

    event_data = {
        "clientId": _string_or_none(raw.get("clientId") or raw.get("client_id"))
        or f"xhs_{index}",
        "eventType": event_type,
        "title": title,
        "startAt": raw.get("startAt") or raw.get("start_at") or None,
        "endAt": raw.get("endAt") or raw.get("end_at") or None,
        "locationName": location_name or title,
        "address": _string_or_none(raw.get("address"), 256),
        "latitude": raw.get("latitude"),
        "longitude": raw.get("longitude"),
        "note": _string_or_none(raw.get("note"), 1000),
        "meta": meta,
        "confidence": confidence,
        "warnings": [str(item) for item in warnings],
        "sortOrder": raw.get("sortOrder") or raw.get("sort_order") or index - 1,
    }

    try:
        return AiTripEventCandidate.model_validate(event_data)
    except ValidationError:
        event_data["startAt"] = None
        event_data["endAt"] = None
        if (event_data["latitude"] is None) != (event_data["longitude"] is None):
            event_data["latitude"] = None
            event_data["longitude"] = None
        try:
            return AiTripEventCandidate.model_validate(event_data)
        except ValidationError:
            return None


def _parse_ai_events(data: dict[str, object]) -> list[AiTripEventCandidate]:
    raw_events = data.get("events")
    if not isinstance(raw_events, list):
        return []
    events: list[AiTripEventCandidate] = []
    for index, raw_event in enumerate(raw_events[:30], start=1):
        candidate = _event_candidate_from_ai(raw_event, index)
        if candidate is not None:
            events.append(candidate)
    return events


def _parse_ai_json(content: str) -> dict[str, object]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise AiClientError("AI response was not valid JSON") from e
    if not isinstance(data, dict):
        raise AiClientError("AI response JSON must be an object")
    return {
        "destination": str(data.get("destination") or "").strip(),
        "note": str(data.get("note") or "").strip(),
        "planDetail": str(data.get("planDetail") or "").strip(),
        "events": _parse_ai_events(data),
    }


def _extracted_text(extracted: dict[str, object], key: str) -> str:
    return str(extracted.get(key) or "").strip()


async def _extract_inspiration_plan(shared_content: str) -> dict[str, object]:
    prompt = f"""
你是旅行计划整理助手。用户粘贴了一个小红书/社媒旅行帖子链接或分享文案。
请从可见内容里整理一个可暂存的旅行灵感，并尽量把具体地点拆成可编辑行程事件。
输出严格 JSON，不要输出 Markdown。

JSON 字段：
- destination: 目的地，尽量短，例如“冰岛”“新西兰南岛”“杭州”
- note: 30 字以内的一句话摘要，适合列表展示
- planDetail: 详细计划，用中文分点，包含建议天数、适合季节、路线/城市、
  亮点、准备提醒。没有信息时基于内容谨慎概括，不要编造具体店名、价格或航班。
- events: 数组，最多 30 个。从帖子里出现的具体地点、景点、餐厅、酒店、交通节点、
  体验项目生成；只有城市名或省份名时不要单独生成 event。帖子有路线顺序时按顺序排列。
  每个 event 字段：
  - eventType: transport|stay|activity|reminder，默认 activity
  - title: 简短事件名，优先使用“动作 + 地点”，没有动作时用地点名
  - startAt/endAt: 有明确日期时间才填 ISO8601，否则填 null
  - locationName/address: 地点名/地址；没有地址不要编造
  - latitude/longitude: 只有内容明确给出坐标才填，否则填 null
  - note: 一句话说明为什么值得加入行程
  - meta: 包含 icon（pin|food|hotel|plane|train|bus|camera|ticket|clock）；
    如果可从行文推断第几天，填 dayOffset，0 表示用户选择开始日期当天
  - confidence: high|medium|low
  - warnings: 缺少时间或地点不明确时写简短中文提示
  - sortOrder: 从 0 开始的顺序

用户内容：
{shared_content[:8000]}
""".strip()
    result = _parse_ai_json(await AiClient().complete_text(prompt=prompt))
    if not result["destination"]:
        raise AiClientError("AI response missing destination")
    return result


async def _extract_share_draft(shared_text: str) -> tuple[dict[str, object], str | None]:
    shared_content, source_url = await _read_shared_content(shared_text)
    try:
        return await _extract_inspiration_plan(shared_content), source_url
    except AiClientError as e:
        detail = str(e)
        status_code = 504 if "timed out" in detail else 502
        raise HTTPException(status_code=status_code, detail=detail) from e


@router.get("", response_model=list[InspirationOut], response_model_by_alias=True)
async def list_inspirations(
    user: CurrentUser, session: SessionDep
) -> list[InspirationOut]:
    stmt = (
        select(TravelInspiration)
        .where(
            TravelInspiration.user_id == user.id,
            TravelInspiration.deleted_at.is_(None),
        )
        .order_by(
            TravelInspiration.status.asc(),
            TravelInspiration.created_at.desc(),
        )
    )
    result = await session.scalars(stmt)
    return [InspirationOut.model_validate(item) for item in result.all()]


@router.post(
    "", response_model=InspirationOut, response_model_by_alias=True, status_code=201
)
async def create_inspiration(
    payload: InspirationCreate, user: CurrentUser, session: SessionDep
) -> InspirationOut:
    item = TravelInspiration(
        user_id=user.id,
        destination=payload.destination,
        type=payload.type.value,
        source_url=payload.source_url,
        note=payload.note,
        plan_detail=payload.plan_detail,
        status="idea",
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return InspirationOut.model_validate(item)


@router.post(
    "/from-share",
    response_model=InspirationOut,
    response_model_by_alias=True,
    status_code=201,
)
async def create_inspiration_from_share(
    payload: InspirationFromShareIn, user: CurrentUser, session: SessionDep
) -> InspirationOut:
    extracted, source_url = await _extract_share_draft(payload.shared_text)

    item = TravelInspiration(
        user_id=user.id,
        destination=_extracted_text(extracted, "destination")[:64],
        type=payload.type.value,
        source_url=source_url,
        note=_extracted_text(extracted, "note")[:500] or None,
        plan_detail=_extracted_text(extracted, "planDetail")[:4000] or None,
        status="idea",
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return InspirationOut.model_validate(item)


@router.post(
    "/from-share/preview",
    response_model=InspirationShareDraftOut,
    response_model_by_alias=True,
)
async def preview_inspiration_from_share(
    payload: InspirationFromShareIn,
    user: CurrentUser,
) -> InspirationShareDraftOut:
    extracted, source_url = await _extract_share_draft(payload.shared_text)
    return InspirationShareDraftOut(
        destination=_extracted_text(extracted, "destination")[:64],
        source_url=source_url,
        note=_extracted_text(extracted, "note")[:500] or None,
        plan_detail=_extracted_text(extracted, "planDetail")[:4000] or None,
        events=list(extracted.get("events") or []),
    )


@router.patch("/{item_id}", response_model=InspirationOut, response_model_by_alias=True)
async def patch_inspiration(
    item_id: UUID,
    payload: InspirationPatch,
    user: CurrentUser,
    session: SessionDep,
) -> InspirationOut:
    item = await session.scalar(
        select(TravelInspiration).where(
            TravelInspiration.id == item_id,
            TravelInspiration.user_id == user.id,
            TravelInspiration.deleted_at.is_(None),
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="inspiration not found")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if hasattr(value, "value"):
            value = value.value
        setattr(item, key, value)

    if updates:
        item.updated_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(item)
    return InspirationOut.model_validate(item)


@router.delete("/{item_id}", status_code=204)
async def delete_inspiration(
    item_id: UUID, user: CurrentUser, session: SessionDep
) -> Response:
    item = await session.scalar(
        select(TravelInspiration).where(
            TravelInspiration.id == item_id,
            TravelInspiration.user_id == user.id,
            TravelInspiration.deleted_at.is_(None),
        )
    )
    if item is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    item.deleted_at = datetime.now(UTC)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
