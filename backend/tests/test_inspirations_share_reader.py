from types import SimpleNamespace

import pytest

from app.routes import inspirations
from app.schemas.inspiration import InspirationFromShareIn
from app.services.xiaohongshu_client import XiaohongshuNoteContent

WILLER_SHARE_TEXT = """
云南旅游图 拿去，不明白的可以问我这个老云南人… http://xhslink.com/o/8YubdGJsrA2
先复制再进入【小红书】，笔记内容马上出现。
""".strip()


@pytest.mark.asyncio
async def test_read_shared_content_uses_xiaohongshu_client(monkeypatch) -> None:
    closed = False

    class FakeXiaohongshuClient:
        async def read_shared_note(self, shared_text: str) -> XiaohongshuNoteContent:
            assert shared_text == WILLER_SHARE_TEXT
            return XiaohongshuNoteContent(
                source_url="http://xhslink.com/o/8YubdGJsrA2",
                final_url="https://www.xiaohongshu.com/explore/yunnan-note",
                title="云南旅游图",
                description="昆明 大理 丽江 香格里拉 7日路线",
                text="云南本地人整理的旅游路线。",
                images=[],
            )

        async def aclose(self) -> None:
            nonlocal closed
            closed = True

    monkeypatch.setattr(inspirations, "XiaohongshuClient", FakeXiaohongshuClient)

    content, source_url = await inspirations._read_shared_content(WILLER_SHARE_TEXT)

    assert source_url == "https://www.xiaohongshu.com/explore/yunnan-note"
    assert "小红书内容" in content
    assert "云南旅游图" in content
    assert closed is True


def test_parse_ai_json_extracts_place_events() -> None:
    parsed = inspirations._parse_ai_json(
        """
        {
          "destination": "云南",
          "note": "本地人路线",
          "planDetail": "昆明 - 大理 - 丽江",
          "events": [
            {
              "locationName": "大理古城",
              "note": "适合下午逛吃",
              "meta": { "dayOffset": 1 }
            },
            {
              "title": "洱海骑行",
              "eventType": "activity",
              "locationName": "洱海生态廊道",
              "confidence": "high",
              "sortOrder": 1
            }
          ]
        }
        """
    )

    assert parsed["events"][0].title == "大理古城"
    assert parsed["events"][0].location_name == "大理古城"
    assert parsed["events"][0].meta["dayOffset"] == 1
    assert parsed["events"][1].title == "洱海骑行"
    assert parsed["events"][1].confidence == "high"


@pytest.mark.asyncio
async def test_preview_inspiration_from_share_does_not_persist(monkeypatch) -> None:
    async def fake_read_shared_content(shared_text: str) -> tuple[str, str | None]:
        assert shared_text == WILLER_SHARE_TEXT
        return "小红书内容：云南旅游图", "https://www.xiaohongshu.com/explore/yunnan-note"

    async def fake_extract_inspiration_plan(shared_content: str) -> dict[str, object]:
        assert "云南旅游图" in shared_content
        return {
            "destination": "云南",
            "note": "本地人路线",
            "planDetail": "昆明 - 大理 - 丽江 - 香格里拉",
            "events": [
                {
                    "clientId": "xhs_1",
                    "eventType": "activity",
                    "title": "大理古城",
                    "startAt": None,
                    "endAt": None,
                    "locationName": "大理古城",
                    "address": None,
                    "latitude": None,
                    "longitude": None,
                    "note": "适合下午逛吃",
                    "meta": {"dayOffset": 1, "icon": "pin"},
                    "confidence": "medium",
                    "warnings": [],
                    "sortOrder": 0,
                }
            ],
        }

    monkeypatch.setattr(inspirations, "_read_shared_content", fake_read_shared_content)
    monkeypatch.setattr(
        inspirations, "_extract_inspiration_plan", fake_extract_inspiration_plan
    )

    result = await inspirations.preview_inspiration_from_share(
        InspirationFromShareIn(sharedText=WILLER_SHARE_TEXT),
        user=SimpleNamespace(),
    )

    assert result.destination == "云南"
    assert result.note == "本地人路线"
    assert result.plan_detail == "昆明 - 大理 - 丽江 - 香格里拉"
    assert result.source_url == "https://www.xiaohongshu.com/explore/yunnan-note"
    assert result.events[0].title == "大理古城"
    assert result.events[0].meta["dayOffset"] == 1
