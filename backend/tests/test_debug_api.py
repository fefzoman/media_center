from collections.abc import Mapping

from fastapi.testclient import TestClient

from media_center.dependencies import get_torrent_backend
from media_center.main import app
from media_center.torrents import (
    TorrentBackend,
    TorrentFile,
    TorrentHandle,
    TorrentStream,
)

INFO_HASH = "08ada5a7a6183aae1e09d831df6748d566095a10"


class DebugBackend(TorrentBackend):
    async def ensure_source(self, torrent_uri: str) -> TorrentHandle:
        assert torrent_uri.startswith("magnet:")
        return TorrentHandle(INFO_HASH)

    async def list_files(self, handle: TorrentHandle) -> list[TorrentFile]:
        return [
            TorrentFile(index=1, path="sample.mkv", length=100),
            TorrentFile(index=2, path="Sintel.mp4", length=1_000),
        ]

    async def get_stream_url(self, handle: TorrentHandle, file_index: int) -> str:
        return f"/play/{handle.info_hash}/{file_index}"

    async def open_stream(
        self,
        handle: TorrentHandle,
        file_index: int,
        request_method: str,
        request_headers: Mapping[str, str],
    ) -> TorrentStream:
        raise NotImplementedError

    async def remove_source(self, handle: TorrentHandle) -> None:
        raise NotImplementedError

    async def health(self) -> bool:
        return True

    async def configure(self, cache_mb: int, use_disk: bool) -> None:
        raise NotImplementedError


def test_debug_play_returns_application_stream_url() -> None:
    app.dependency_overrides[get_torrent_backend] = DebugBackend
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/debug/play",
                json={"torrent_uri": "magnet:?xt=urn:btih:authorized-test"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "stream_url": f"/play/{INFO_HASH}/2",
        "file": "Sintel.mp4",
        "status": "ready",
    }
