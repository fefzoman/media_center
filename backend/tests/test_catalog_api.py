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


class CatalogBackend(TorrentBackend):
    def __init__(self) -> None:
        self.received_uri: str | None = None

    async def ensure_source(self, torrent_uri: str) -> TorrentHandle:
        self.received_uri = torrent_uri
        return TorrentHandle(INFO_HASH)

    async def list_files(self, handle: TorrentHandle) -> list[TorrentFile]:
        return [TorrentFile(index=6, path="Sintel/Sintel.mp4", length=129_241_752)]

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


def test_catalog_lists_seed_without_exposing_source() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/movies")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "sintel",
            "title": "Sintel",
            "year": 2010,
            "poster_url": "/tv/assets/posters/sintel.svg",
            "progress": 0.0,
        }
    ]
    assert "torrent" not in response.text.lower()


def test_catalog_returns_movie_details_and_not_found() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/movies/sintel")
        missing = client.get("/api/v1/movies/missing")

    assert response.status_code == 200
    assert response.json()["runtime_seconds"] == 888
    assert response.json()["description"]
    assert "torrent_uri" not in response.text
    assert missing.status_code == 404


def test_catalog_movie_starts_without_source_from_frontend() -> None:
    backend = CatalogBackend()
    app.dependency_overrides[get_torrent_backend] = lambda: backend
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/movies/sintel/play",
                json={
                    "client_id": "test-tv",
                    "capabilities": {
                        "h264": True,
                        "hevc": True,
                        "aac": True,
                        "hls": True,
                    },
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["session_id"].startswith("session_")
    assert response.json()["mode"] == "direct"
    assert response.json()["url"] == f"/play/{INFO_HASH}/6"
    assert response.json()["resume_position_seconds"] == 0
    assert backend.received_uri == "https://example.invalid/authorized.torrent"
