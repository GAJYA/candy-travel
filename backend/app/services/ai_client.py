from __future__ import annotations

import base64

import httpx

from app.config import settings


class AiClientError(Exception):
    """Raised when the OpenAI-compatible AI endpoint fails."""


class AiClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self.base_url = (base_url or settings.ai_base_url).rstrip("/")
        self.api_key = api_key or settings.ai_api_key
        self.model = model or settings.ai_model
        self.timeout_seconds = timeout_seconds or settings.ai_timeout_seconds

    async def describe_images(self, *, prompt: str, images: list[tuple[bytes, str]]) -> str:
        if not self.base_url or not self.api_key:
            raise AiClientError("AI service is not configured")
        if not images:
            raise AiClientError("at least one image is required")

        content: list[dict[str, object]] = [{"type": "text", "text": prompt}]
        for image_bytes, media_type in images:
            encoded = base64.b64encode(image_bytes).decode("ascii")
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{media_type};base64,{encoded}"},
                }
            )

        payload = {
            "model": self.model,
            "stream": False,
            "messages": [{"role": "user", "content": content}],
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
        except httpx.TimeoutException as e:
            raise AiClientError("AI request timed out") from e
        except httpx.HTTPStatusError as e:
            raise AiClientError(f"AI request failed with HTTP {e.response.status_code}") from e
        except httpx.HTTPError as e:
            raise AiClientError("AI request failed") from e

        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise AiClientError("AI response missing message content") from e
