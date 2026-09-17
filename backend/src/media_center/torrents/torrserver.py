"""TorrServer-LT adapter. No other module calls the TorrServer API directly."""

import asyncio
import re
import time
from collections.abc import Mapping
from typing import Any

import httpx

from media_center.torrents.base import (
    TorrentBackend,
    TorrentBackendUnavailable,
    TorrentFile,
    TorrentHandle,
    TorrentMetadataTimeout,
    TorrentProtocolError,
    TorrentStream,
)

INFO_HASH_PATTERN = re.compile(r"^[0-9a-f]{40}$")
FORWARDED_REQUEST_HEADERS = frozenset(
    {"range", "if-range", "if-none-match", "user-agent", "accept"}
)


class TorrServerBackend(TorrentBackend):
    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        metadata_timeout_seconds: float = 120.0,
        poll_interval_seconds: float = 1.0,
    ) -> None:
        self._client = client
        self._metadata_timeout_seconds = metadata_timeout_seconds
        self._poll_interval_seconds = poll_interval_seconds

    async def ensure_source(self, torrent_uri: str) -> TorrentHandle:
        payload = await self._post_json(
            "/torrents",
            {"action": "add", "link": torrent_uri, "save_to_db": False},
        )
        handle = self._parse_handle(payload)
        deadline = time.monotonic() + self._metadata_timeout_seconds

        while True:
            files = self._parse_files(payload)
            if files:
                return handle
            if time.monotonic() >= deadline:
                raise TorrentMetadataTimeout(
                    "Torrent metadata was not available before the timeout."
                )
            await asyncio.sleep(self._poll_interval_seconds)
            payload = await self._post_json(
                "/torrents", {"action": "get", "hash": handle.info_hash}
            )

    async def list_files(self, handle: TorrentHandle) -> list[TorrentFile]:
        payload = await self._post_json(
            "/torrents", {"action": "get", "hash": handle.info_hash}
        )
        return self._parse_files(payload)

    async def get_stream_url(self, handle: TorrentHandle, file_index: int) -> str:
        self._validate_handle(handle)
        if file_index < 1:
            raise TorrentProtocolError("TorrServer file indexes must be positive.")
        return f"/play/{handle.info_hash}/{file_index}"

    async def open_stream(
        self,
        handle: TorrentHandle,
        file_index: int,
        request_method: str,
        request_headers: Mapping[str, str],
    ) -> TorrentStream:
        self._validate_handle(handle)
        if file_index < 1:
            raise TorrentProtocolError("TorrServer file indexes must be positive.")
        headers = {
            name: value
            for name, value in request_headers.items()
            if name.lower() in FORWARDED_REQUEST_HEADERS
        }
        request = self._client.build_request(
            request_method,
            f"/play/{handle.info_hash}/{file_index}",
            headers=headers,
        )
        try:
            response = await self._client.send(request, stream=True)
        except httpx.HTTPError as exc:
            raise TorrentBackendUnavailable(
                "TorrServer stream is unavailable."
            ) from exc
        return TorrentStream(
            status_code=response.status_code,
            headers=response.headers,
            body=response.aiter_raw(),
            close=response.aclose,
        )

    async def remove_source(self, handle: TorrentHandle) -> None:
        self._validate_handle(handle)
        await self._post_empty(
            "/torrents", {"action": "drop", "hash": handle.info_hash}
        )

    async def health(self) -> bool:
        try:
            response = await self._client.get("/echo")
            return response.status_code == httpx.codes.OK
        except httpx.HTTPError:
            return False

    async def configure(self, cache_mb: int, use_disk: bool) -> None:
        gst_response = await self._request("GET", "/gst/settings")
        try:
            gst_status = gst_response.json()
        except ValueError as exc:
            raise TorrentProtocolError(
                "TorrServer returned invalid GStreamer status."
            ) from exc
        if not isinstance(gst_status, dict) or gst_status.get("built_in") is not True:
            raise TorrentProtocolError(
                "TorrServer was not built with GStreamer support."
            )

        current = await self._post_json("/settings", {"action": "get"})
        if not isinstance(current, dict):
            raise TorrentProtocolError("TorrServer settings response is invalid.")
        expected_cache = cache_mb * 1024 * 1024
        desired = dict(current)
        desired["CacheSize"] = expected_cache
        desired["UseDisk"] = use_disk
        await self._post_empty("/settings", {"action": "set", "sets": desired})
        actual = await self._post_json("/settings", {"action": "get"})
        if (
            not isinstance(actual, dict)
            or actual.get("CacheSize") != expected_cache
            or actual.get("UseDisk") is not use_disk
        ):
            raise TorrentProtocolError("TorrServer did not apply required settings.")

    async def _post_json(self, path: str, payload: dict[str, Any]) -> Any:
        response = await self._request("POST", path, json=payload)
        try:
            return response.json()
        except ValueError as exc:
            raise TorrentProtocolError("TorrServer returned invalid JSON.") from exc

    async def _post_empty(self, path: str, payload: dict[str, Any]) -> None:
        await self._request("POST", path, json=payload)

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            response = await self._client.request(method, path, **kwargs)
            response.raise_for_status()
            return response
        except httpx.RequestError as exc:
            raise TorrentBackendUnavailable("TorrServer is unavailable.") from exc
        except httpx.HTTPStatusError as exc:
            raise TorrentProtocolError(
                f"TorrServer returned HTTP {exc.response.status_code}."
            ) from exc

    @staticmethod
    def _parse_handle(payload: Any) -> TorrentHandle:
        if not isinstance(payload, dict):
            raise TorrentProtocolError("TorrServer torrent response is invalid.")
        info_hash = str(payload.get("hash", "")).lower()
        handle = TorrentHandle(info_hash=info_hash)
        TorrServerBackend._validate_handle(handle)
        return handle

    @staticmethod
    def _validate_handle(handle: TorrentHandle) -> None:
        if INFO_HASH_PATTERN.fullmatch(handle.info_hash) is None:
            raise TorrentProtocolError("TorrServer returned an invalid info hash.")

    @staticmethod
    def _parse_files(payload: Any) -> list[TorrentFile]:
        if not isinstance(payload, dict):
            raise TorrentProtocolError("TorrServer torrent response is invalid.")
        raw_files = payload.get("file_stats") or []
        if not isinstance(raw_files, list):
            raise TorrentProtocolError("TorrServer file list is invalid.")
        files: list[TorrentFile] = []
        try:
            for raw_file in raw_files:
                index = int(raw_file["id"])
                path = str(raw_file["path"])
                length = int(raw_file["length"])
                if index < 1 or not path or length < 0:
                    raise ValueError
                files.append(TorrentFile(index=index, path=path, length=length))
        except (KeyError, TypeError, ValueError) as exc:
            raise TorrentProtocolError("TorrServer file entry is invalid.") from exc
        return files
