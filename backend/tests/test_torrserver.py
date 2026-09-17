import asyncio
import json

import httpx
import pytest

from media_center.torrents import (
    TorrentHandle,
    TorrentMetadataTimeout,
    TorrentProtocolError,
    TorrServerBackend,
)

INFO_HASH = "08ada5a7a6183aae1e09d831df6748d566095a10"


def make_client(handler: httpx.MockTransport) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=handler, base_url="http://torrserver:8090")


def test_registers_ephemeral_source_and_parses_files() -> None:
    requests: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        requests.append(payload)
        if payload["action"] == "add":
            return httpx.Response(200, json={"hash": INFO_HASH})
        return httpx.Response(
            200,
            json={
                "hash": INFO_HASH,
                "file_stats": [{"id": 1, "path": "Sintel.mp4", "length": 129_241_752}],
            },
        )

    async def exercise() -> None:
        async with make_client(httpx.MockTransport(handler)) as client:
            backend = TorrServerBackend(
                client, metadata_timeout_seconds=1, poll_interval_seconds=0.001
            )
            handle = await backend.ensure_source("magnet:?xt=urn:btih:test")
            files = await backend.list_files(handle)
            assert handle == TorrentHandle(INFO_HASH)
            assert files[0].path == "Sintel.mp4"
            assert files[0].index == 1

    asyncio.run(exercise())
    assert requests[0] == {
        "action": "add",
        "link": "magnet:?xt=urn:btih:test",
        "save_to_db": False,
    }
    assert requests[1] == {"action": "get", "hash": INFO_HASH}


def test_metadata_timeout_is_explicit() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"hash": INFO_HASH})

    async def exercise() -> None:
        async with make_client(httpx.MockTransport(handler)) as client:
            backend = TorrServerBackend(
                client, metadata_timeout_seconds=0.001, poll_interval_seconds=0.002
            )
            with pytest.raises(TorrentMetadataTimeout):
                await backend.ensure_source("magnet:?xt=urn:btih:test")

    asyncio.run(exercise())


def test_configures_and_verifies_ram_cache_and_gstreamer_build() -> None:
    settings = {"CacheSize": 64 * 1024 * 1024, "UseDisk": True, "EnableDHT": True}
    set_payload: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal settings, set_payload
        if request.url.path == "/gst/settings":
            return httpx.Response(200, json={"built_in": True})
        payload = json.loads(request.content)
        if payload["action"] == "get":
            return httpx.Response(200, json=settings)
        set_payload = payload
        settings = payload["sets"]
        return httpx.Response(200)

    async def exercise() -> None:
        async with make_client(httpx.MockTransport(handler)) as client:
            await TorrServerBackend(client).configure(1024, False)

    asyncio.run(exercise())
    assert set_payload["sets"] == {
        "CacheSize": 1024 * 1024 * 1024,
        "UseDisk": False,
        "EnableDHT": True,
    }


def test_rejects_non_gstreamer_binary() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"built_in": False})

    async def exercise() -> None:
        async with make_client(httpx.MockTransport(handler)) as client:
            with pytest.raises(TorrentProtocolError, match="GStreamer"):
                await TorrServerBackend(client).configure(1024, False)

    asyncio.run(exercise())


def test_stream_forwards_range_without_exposing_source_uri() -> None:
    captured: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured
        captured = request
        return httpx.Response(
            206,
            headers={"Content-Range": "bytes 10-12/20"},
            stream=httpx.ByteStream(b"abc"),
        )

    async def exercise() -> None:
        async with make_client(httpx.MockTransport(handler)) as client:
            backend = TorrServerBackend(client)
            handle = TorrentHandle(INFO_HASH)
            assert await backend.get_stream_url(handle, 1) == f"/play/{INFO_HASH}/1"
            stream = await backend.open_stream(
                handle, 1, "GET", {"range": "bytes=10-12", "cookie": "secret"}
            )
            assert stream.status_code == 206
            assert b"".join([part async for part in stream.body]) == b"abc"
            await stream.close()

    asyncio.run(exercise())
    assert captured is not None
    assert captured.url.path == f"/play/{INFO_HASH}/1"
    assert captured.headers["range"] == "bytes=10-12"
    assert "cookie" not in captured.headers
