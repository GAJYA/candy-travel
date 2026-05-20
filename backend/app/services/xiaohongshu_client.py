from __future__ import annotations

import re
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlparse

import httpx


class XiaohongshuClientError(Exception):
    """Raised when a Xiaohongshu share URL cannot be read safely."""


URL_RE = re.compile(r"https?://[^\s<>'\"]+")
TRAILING_URL_CHARS = "，。,.),）]】」"
ALLOWED_HOSTS = {
    "xhslink.com",
    "www.xhslink.com",
    "xhs.cn",
    "www.xhs.cn",
    "xiaohongshu.com",
    "www.xiaohongshu.com",
    "m.xiaohongshu.com",
}


@dataclass(frozen=True)
class XiaohongshuNoteContent:
    source_url: str
    final_url: str
    title: str | None
    description: str | None
    text: str
    images: list[str]

    def to_prompt_text(self) -> str:
        parts = [
            f"sourceUrl: {self.source_url}",
            f"finalUrl: {self.final_url}",
        ]
        if self.title:
            parts.append(f"title: {self.title}")
        if self.description:
            parts.append(f"description: {self.description}")
        if self.text:
            parts.append(f"text: {self.text}")
        if self.images:
            parts.append(f"images: {', '.join(self.images[:6])}")
        return "\n".join(parts)


class _HtmlMetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, str] = {}
        self.images: list[str] = []
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self._in_title = False
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
            return
        if tag == "title":
            self._in_title = True
            return
        if tag != "meta":
            return

        attr_map = {key.lower(): value or "" for key, value in attrs}
        key = (attr_map.get("property") or attr_map.get("name") or "").lower()
        content = _clean_text(attr_map.get("content", ""))
        if not key or not content:
            return
        self.meta.setdefault(key, content)
        if key in {"og:image", "twitter:image"} and content not in self.images:
            self.images.append(content)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"} and self._skip_depth > 0:
            self._skip_depth -= 1
            return
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        text = _clean_text(data)
        if not text or self._skip_depth > 0:
            return
        if self._in_title:
            self.title_parts.append(text)
        else:
            self.text_parts.append(text)


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", unescape(text)).strip()


def _dedupe_parts(parts: list[str | None]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for part in parts:
        text = _clean_text(part or "")
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def extract_share_url(text: str) -> str | None:
    match = URL_RE.search(text)
    if match is None:
        return None
    return match.group(0).rstrip(TRAILING_URL_CHARS)


def is_xiaohongshu_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in {"http", "https"}:
        return False
    host = (parsed.hostname or "").lower()
    return host in ALLOWED_HOSTS or host.endswith(".xiaohongshu.com")


def parse_xiaohongshu_html(
    html: str, *, source_url: str, final_url: str
) -> XiaohongshuNoteContent:
    parser = _HtmlMetadataParser()
    parser.feed(html)

    title = next(
        (
            item
            for item in [
                parser.meta.get("og:title"),
                parser.meta.get("twitter:title"),
                _clean_text(" ".join(parser.title_parts)),
            ]
            if item
        ),
        None,
    )
    description = next(
        (
            item
            for item in [
                parser.meta.get("og:description"),
                parser.meta.get("description"),
                parser.meta.get("twitter:description"),
            ]
            if item
        ),
        None,
    )
    visible_text = _clean_text(" ".join(parser.text_parts))
    text = "\n".join(_dedupe_parts([title, description, visible_text]))[:8000]

    return XiaohongshuNoteContent(
        source_url=source_url,
        final_url=final_url,
        title=title,
        description=description,
        text=text,
        images=parser.images,
    )


class XiaohongshuClient:
    def __init__(
        self,
        *,
        http_client: httpx.AsyncClient | None = None,
        timeout_seconds: float = 12,
    ) -> None:
        self._client = http_client
        self._owns_client = http_client is None
        self._timeout_seconds = timeout_seconds

    async def read_shared_note(self, shared_text: str) -> XiaohongshuNoteContent:
        source_url = extract_share_url(shared_text) or shared_text.strip()
        if not is_xiaohongshu_url(source_url):
            raise XiaohongshuClientError("unsupported xiaohongshu url")

        response = await self._get(source_url)
        final_url = str(response.url)
        if not is_xiaohongshu_url(final_url):
            raise XiaohongshuClientError("xiaohongshu redirect target is not allowed")

        note = parse_xiaohongshu_html(
            response.text,
            source_url=source_url,
            final_url=final_url,
        )
        if len(note.text) < 20:
            raise XiaohongshuClientError("xiaohongshu page did not expose readable content")
        return note

    async def _get(self, url: str) -> httpx.Response:
        client = self._client
        if client is None:
            client = httpx.AsyncClient(
                timeout=self._timeout_seconds,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/125.0 Safari/537.36"
                    ),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
                },
            )
            self._client = client

        try:
            response = await client.get(url)
            response.raise_for_status()
        except httpx.TimeoutException as e:
            raise XiaohongshuClientError("xiaohongshu request timed out") from e
        except httpx.HTTPStatusError as e:
            raise XiaohongshuClientError(
                f"xiaohongshu request failed with HTTP {e.response.status_code}"
            ) from e
        except httpx.HTTPError as e:
            raise XiaohongshuClientError("xiaohongshu request failed") from e
        return response

    async def aclose(self) -> None:
        if self._client is not None and self._owns_client:
            await self._client.aclose()
