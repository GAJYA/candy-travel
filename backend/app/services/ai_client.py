from __future__ import annotations

import asyncio
import base64
from typing import Any

import httpx

from app.config import settings


class AiClientError(Exception):
    """Raised when the OpenAI-compatible AI endpoint fails."""


def extract_message_content(data: dict[str, Any]) -> str:
    output_text = data.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise AiClientError("AI response missing message content")

    choice = choices[0]
    if not isinstance(choice, dict):
        raise AiClientError("AI response missing message content")

    message = choice.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str):
                        parts.append(text)
                    elif isinstance(text, dict) and isinstance(text.get("value"), str):
                        parts.append(text["value"])
            if parts:
                return "".join(parts)

    text = choice.get("text")
    if isinstance(text, str) and text.strip():
        return text

    raise AiClientError("AI response missing message content")


class AiClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        reasoning_effort: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self.base_url = (base_url or settings.ai_base_url).rstrip("/")
        self.api_key = api_key or settings.ai_api_key
        self.model = model or settings.ai_model
        self.reasoning_effort = reasoning_effort or settings.ai_reasoning_effort
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
            "reasoning_effort": self.reasoning_effort,
            "stream": False,
            "messages": [{"role": "user", "content": content}],
        }

        last_content_error: AiClientError | None = None
        for attempt in range(3):
            data = await self._post_chat_completion(payload)
            try:
                return extract_message_content(data)
            except AiClientError as e:
                last_content_error = e
                if attempt < 2:
                    await asyncio.sleep(0.4 * (attempt + 1))

        if last_content_error is not None:
            raise last_content_error
        raise AiClientError("AI response missing message content")

    async def complete_text(self, *, prompt: str) -> str:
        if not self.base_url or not self.api_key:
            raise AiClientError("AI service is not configured")

        payload = {
            "model": self.model,
            "reasoning_effort": self.reasoning_effort,
            "stream": False,
            "messages": [{"role": "user", "content": prompt}],
        }

        data = await self._post_chat_completion(payload)
        return extract_message_content(data)

    async def _post_chat_completion(self, payload: dict[str, object]) -> dict[str, Any]:
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

        try:
            data = response.json()
        except ValueError as e:
            raise AiClientError("AI response was not JSON") from e
        if not isinstance(data, dict):
            raise AiClientError("AI response must be a JSON object")
        return data
