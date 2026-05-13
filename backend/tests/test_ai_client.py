import pytest

from app.services.ai_client import AiClient, AiClientError, extract_message_content


def test_extract_message_content_accepts_string_content():
    content = extract_message_content(
        {"choices": [{"message": {"role": "assistant", "content": "pong"}}]}
    )

    assert content == "pong"


def test_extract_message_content_accepts_list_content():
    content = extract_message_content(
        {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": [{"type": "text", "text": "pong"}],
                    }
                }
            ]
        }
    )

    assert content == "pong"


def test_extract_message_content_raises_on_missing_content():
    with pytest.raises(AiClientError, match="AI response missing message content"):
        extract_message_content({"choices": [{"message": {"role": "assistant"}}]})


@pytest.mark.asyncio
async def test_describe_images_retries_missing_message_content(monkeypatch):
    class FakeResponse:
        def __init__(self, data):
            self.data = data

        def raise_for_status(self):
            return None

        def json(self):
            return self.data

    class FakeAsyncClient:
        calls = 0

        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, *args, **kwargs):
            FakeAsyncClient.calls += 1
            if FakeAsyncClient.calls == 1:
                return FakeResponse({"choices": [{"message": {"role": "assistant"}}]})
            return FakeResponse({"choices": [{"message": {"content": "ok"}}]})

    monkeypatch.setattr("app.services.ai_client.httpx.AsyncClient", FakeAsyncClient)

    content = await AiClient(
        base_url="https://ai.example.test/v1",
        api_key="test-key",
        model="gpt-5.5",
    ).describe_images(prompt="test", images=[(b"image", "image/png")])

    assert content == "ok"
    assert FakeAsyncClient.calls == 2
