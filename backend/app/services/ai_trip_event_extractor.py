from __future__ import annotations

import json
import re
from datetime import date
from typing import Any

from pydantic import ValidationError

from app.config import settings
from app.models import Trip
from app.schemas.ai_import import AiTripEventCandidate
from app.services.ai_client import AiClient, AiClientError


class AiExtractionError(Exception):
    """Raised when the AI response cannot be converted into trip event candidates."""


_PHONE_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
_ID_CARD_RE = re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")
_AMOUNT_RE = re.compile(r"(订单金额|支付金额|实付|总价|票价)[:：]?\s*[0-9.,]+元?")


def sanitize_sensitive_text(text: str | None) -> str | None:
    if not text:
        return text
    sanitized = _PHONE_RE.sub("[手机号已省略]", text)
    sanitized = _ID_CARD_RE.sub("[身份证号已省略]", sanitized)
    sanitized = _AMOUNT_RE.sub("[金额已省略]", sanitized)
    return sanitized


def build_trip_event_prompt(
    *,
    trip_title: str,
    start_date: date | str | None,
    end_date: date | str | None,
    timezone: str,
) -> str:
    return f"""
你是 CandyTravel 的订单截图识别助手。
请从用户上传的飞机、高铁、酒店订单截图中提取可以加入旅行日程的事件。

当前行程：
- 标题：{trip_title}
- 开始日期：{start_date or "未设置"}
- 结束日期：{end_date or "未设置"}
- 默认时区：{timezone}

要求：
- 只返回 JSON，不输出 Markdown，不要包裹代码块。
- 忽略身份证、手机号、支付金额、银行卡号、完整订单号等敏感信息。
- 优先识别飞机、高铁、酒店订单。
- 缺少日期、时间或地点时仍可返回候选项。
- warnings 必须说明缺失字段，confidence 使用 low 或 medium。
- 时间必须使用 ISO 8601 字符串，并尽量带上截图或行程能推断出的时区。
- 酒店入住事件使用全天事件，startAt 为入住日 00:00，endAt 为离店日 00:00。

返回格式：
{{
  "events": [
    {{
      "eventType": "transport|stay|activity|reminder",
      "title": "事件标题",
      "startAt": "ISO8601 或 null",
      "endAt": "ISO8601 或 null",
      "locationName": "地点名或 null",
      "address": "地址或 null",
      "note": "非敏感摘要或 null",
      "meta": {{
        "icon": "plane|train|hotel|ticket|clock|pin",
        "allDay": false,
        "orderType": "flight|train|hotel|other"
      }},
      "confidence": "high|medium|low",
      "warnings": []
    }}
  ],
  "warnings": []
}}
""".strip()


def parse_ai_event_response(content: str) -> tuple[list[AiTripEventCandidate], list[str]]:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as e:
        raise AiExtractionError("AI returned invalid JSON") from e

    if not isinstance(payload, dict):
        raise AiExtractionError("AI response must be a JSON object")

    raw_events = payload.get("events")
    if not isinstance(raw_events, list):
        raise AiExtractionError("AI response missing events list")

    events: list[AiTripEventCandidate] = []
    for index, raw_event in enumerate(raw_events, start=1):
        if not isinstance(raw_event, dict):
            raise AiExtractionError("AI event must be a JSON object")
        event_data: dict[str, Any] = {
            **raw_event,
            "clientId": raw_event.get("clientId") or f"tmp_{index}",
            "note": sanitize_sensitive_text(raw_event.get("note")),
        }
        try:
            events.append(AiTripEventCandidate.model_validate(event_data))
        except ValidationError as e:
            raise AiExtractionError(f"AI event {index} failed validation") from e

    warnings = payload.get("warnings") or []
    if not isinstance(warnings, list):
        warnings = ["AI returned warnings in an invalid format"]
    return events, [str(item) for item in warnings]


async def extract_trip_events(
    *,
    trip: Trip,
    images: list[tuple[bytes, str]],
    client_timezone: str | None = None,
) -> tuple[list[AiTripEventCandidate], list[str], str]:
    timezone = client_timezone or trip.timezone or "Asia/Shanghai"
    prompt = build_trip_event_prompt(
        trip_title=trip.title,
        start_date=trip.start_date,
        end_date=trip.end_date,
        timezone=timezone,
    )
    client = AiClient(model=settings.ai_model)
    try:
        content = await client.describe_images(prompt=prompt, images=images)
    except AiClientError as e:
        if "missing message content" in str(e):
            return [], ["AI 未返回可解析内容，请换一张更清晰的订单截图后重试。"], client.model
        raise
    events, warnings = parse_ai_event_response(content)
    return events, warnings, client.model
