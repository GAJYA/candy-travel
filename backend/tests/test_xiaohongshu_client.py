import httpx
import pytest

from app.services.xiaohongshu_client import (
    XiaohongshuClient,
    XiaohongshuClientError,
    extract_share_url,
    is_xiaohongshu_url,
)

WILLER_SHARE_TEXT = """
云南旅游图 拿去，不明白的可以问我这个老云南人… http://xhslink.com/o/8YubdGJsrA2
先复制再进入【小红书】，笔记内容马上出现。
""".strip()


def test_extract_share_url_handles_xiaohongshu_share_text() -> None:
    assert extract_share_url(WILLER_SHARE_TEXT) == "http://xhslink.com/o/8YubdGJsrA2"


def test_url_guard_only_allows_xiaohongshu_hosts() -> None:
    assert is_xiaohongshu_url("http://xhslink.com/o/8YubdGJsrA2")
    assert is_xiaohongshu_url("https://www.xiaohongshu.com/explore/abc123")
    assert not is_xiaohongshu_url("https://example.com/o/8YubdGJsrA2")


@pytest.mark.asyncio
async def test_read_shared_note_resolves_short_link_and_extracts_metadata() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "http://xhslink.com/o/8YubdGJsrA2"
        return httpx.Response(
            200,
            request=request,
            text="""
            <html>
              <head>
                <title>云南旅游图 - 小红书</title>
                <meta property="og:title" content="云南旅游图" />
                <meta property="og:description" content="昆明 大理 丽江 香格里拉 7日路线" />
                <meta property="og:image" content="https://ci.xiaohongshu.com/image.jpg" />
              </head>
              <body>
                <main>本地人建议：先昆明，再大理，最后丽江和香格里拉。</main>
                <script>window.__INITIAL_STATE__ = {}</script>
              </body>
            </html>
            """,
            headers={"content-type": "text/html"},
        )

    client = XiaohongshuClient(
        http_client=httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="https://example.test",
            follow_redirects=True,
        )
    )

    note = await client.read_shared_note(WILLER_SHARE_TEXT)

    assert note.source_url == "http://xhslink.com/o/8YubdGJsrA2"
    assert note.final_url == "http://xhslink.com/o/8YubdGJsrA2"
    assert note.title == "云南旅游图"
    assert note.description == "昆明 大理 丽江 香格里拉 7日路线"
    assert note.images == ["https://ci.xiaohongshu.com/image.jpg"]
    assert "先昆明，再大理" in note.text
    assert "window.__INITIAL_STATE__" not in note.text

    await client.aclose()


@pytest.mark.asyncio
async def test_read_shared_note_rejects_non_xiaohongshu_url() -> None:
    client = XiaohongshuClient(
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(lambda request: None))
    )

    with pytest.raises(XiaohongshuClientError, match="unsupported xiaohongshu url"):
        await client.read_shared_note("https://example.com/travel")

    await client.aclose()
