import json
import re
from datetime import UTC, datetime
from uuid import UUID

import httpx
from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.deps import CurrentUser, SessionDep
from app.models import TravelInspiration
from app.schemas.inspiration import (
    InspirationCreate,
    InspirationFromShareIn,
    InspirationOut,
    InspirationPatch,
)
from app.services.ai_client import AiClient, AiClientError

router = APIRouter(prefix="/inspirations", tags=["inspirations"])

URL_RE = re.compile(r"https?://[^\s]+")


def _extract_url(text: str) -> str | None:
    match = URL_RE.search(text)
    if not match:
        return None
    return match.group(0).rstrip("，。),）]")


def _clean_page_text(html: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;?", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:6000]


async def _read_shared_content(shared_text: str) -> tuple[str, str | None]:
    source_url = _extract_url(shared_text)
    if not source_url:
        return shared_text, None

    try:
        async with httpx.AsyncClient(
            timeout=12,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/125 Safari/537.36"
                )
            },
        ) as client:
            response = await client.get(source_url)
            response.raise_for_status()
    except httpx.HTTPError:
        return shared_text, source_url

    page_text = _clean_page_text(response.text)
    if len(page_text) < 80:
        return shared_text, str(response.url)
    return f"{shared_text}\n\n网页内容：\n{page_text}", str(response.url)


def _parse_ai_json(content: str) -> dict[str, str]:
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
    }


async def _extract_inspiration_plan(shared_content: str) -> dict[str, str]:
    prompt = f"""
你是旅行计划整理助手。用户粘贴了一个小红书/社媒旅行帖子链接或分享文案。
请从可见内容里整理一个可暂存的旅行灵感，输出严格 JSON，不要输出 Markdown。

JSON 字段：
- destination: 目的地，尽量短，例如“冰岛”“新西兰南岛”“杭州”
- note: 30 字以内的一句话摘要，适合列表展示
- planDetail: 详细计划，用中文分点，包含建议天数、适合季节、路线/城市、亮点、准备提醒。没有信息时基于内容谨慎概括，不要编造具体店名、价格或航班。

用户内容：
{shared_content[:8000]}
""".strip()
    result = _parse_ai_json(await AiClient().complete_text(prompt=prompt))
    if not result["destination"]:
        raise AiClientError("AI response missing destination")
    return result


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
    shared_content, source_url = await _read_shared_content(payload.shared_text)
    try:
        extracted = await _extract_inspiration_plan(shared_content)
    except AiClientError as e:
        detail = str(e)
        status_code = 504 if "timed out" in detail else 502
        raise HTTPException(status_code=status_code, detail=detail) from e

    item = TravelInspiration(
        user_id=user.id,
        destination=extracted["destination"][:64],
        type=payload.type.value,
        source_url=source_url,
        note=extracted["note"][:500] or None,
        plan_detail=extracted["planDetail"][:4000] or None,
        status="idea",
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return InspirationOut.model_validate(item)


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
