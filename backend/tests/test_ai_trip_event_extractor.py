import json
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas.ai_import import AiTripEventCandidate
from app.services.ai_client import AiClientError
from app.services.ai_trip_event_extractor import (
    AiExtractionError,
    build_trip_event_prompt,
    extract_trip_events,
    parse_ai_event_response,
    sanitize_sensitive_text,
)


def test_candidate_accepts_transport_payload():
    candidate = AiTripEventCandidate.model_validate(
        {
            "clientId": "tmp_1",
            "eventType": "transport",
            "title": "航班 MU123 上海虹桥 -> 东京羽田",
            "startAt": "2026-05-20T09:30:00+08:00",
            "endAt": "2026-05-20T12:45:00+09:00",
            "locationName": "上海虹桥国际机场",
            "address": None,
            "note": "到达：东京羽田机场",
            "meta": {
                "icon": "plane",
                "allDay": False,
                "orderType": "flight",
                "transportMode": "flight",
            },
            "confidence": "high",
            "warnings": [],
        }
    )

    assert candidate.event_type == "transport"
    assert candidate.client_id == "tmp_1"
    assert candidate.confidence == "high"


def test_candidate_rejects_invalid_event_type():
    with pytest.raises(ValidationError):
        AiTripEventCandidate.model_validate(
            {
                "clientId": "tmp_1",
                "eventType": "invoice",
                "title": "发票",
                "startAt": "2026-05-20T09:30:00+08:00",
                "meta": {},
                "confidence": "low",
                "warnings": [],
            }
        )


def test_parse_ai_event_response_returns_candidates():
    content = json.dumps(
        {
            "events": [
                {
                    "eventType": "stay",
                    "title": "入住新宿酒店",
                    "startAt": "2026-05-20T00:00:00+09:00",
                    "endAt": "2026-05-23T00:00:00+09:00",
                    "locationName": "新宿酒店",
                    "address": "东京都新宿区",
                    "note": "高级双床房",
                    "meta": {"icon": "hotel", "allDay": True, "orderType": "hotel"},
                    "confidence": "high",
                    "warnings": [],
                }
            ],
            "warnings": [],
        },
        ensure_ascii=False,
    )

    events, warnings = parse_ai_event_response(content)

    assert warnings == []
    assert events[0].client_id == "tmp_1"
    assert events[0].event_type == "stay"
    assert events[0].meta["icon"] == "hotel"


def test_parse_ai_event_response_rejects_non_json():
    with pytest.raises(AiExtractionError, match="AI returned invalid JSON"):
        parse_ai_event_response("```json\n{}\n```")


def test_sanitize_sensitive_text_masks_personal_data():
    text = "乘机人张三，手机号 13812345678，身份证 110101199001011234，订单金额 1234 元"

    sanitized = sanitize_sensitive_text(text)

    assert sanitized is not None
    assert "13812345678" not in sanitized
    assert "110101199001011234" not in sanitized
    assert "订单金额" not in sanitized
    assert "乘机人张三" in sanitized


def test_build_trip_event_prompt_contains_trip_context():
    prompt = build_trip_event_prompt(
        trip_title="东京旅行",
        start_date="2026-05-20",
        end_date="2026-05-23",
        timezone="Asia/Tokyo",
    )

    assert "东京旅行" in prompt
    assert "2026-05-20" in prompt
    assert "Asia/Tokyo" in prompt
    assert "只返回 JSON" in prompt


@pytest.mark.asyncio
async def test_extract_trip_events_downgrades_empty_ai_content(monkeypatch):
    async def fake_describe_images(self, *, prompt, images):
        raise AiClientError("AI response missing message content")

    monkeypatch.setattr("app.services.ai_client.AiClient.describe_images", fake_describe_images)
    trip = SimpleNamespace(
        title="东京旅行",
        start_date="2026-05-20",
        end_date="2026-05-23",
        timezone="Asia/Tokyo",
    )

    events, warnings, model = await extract_trip_events(
        trip=trip,
        images=[(b"image", "image/png")],
    )

    assert model == "gpt-5.5"
    assert events == []
    assert warnings == ["AI 未返回可解析内容，请换一张更清晰的订单截图后重试。"]
