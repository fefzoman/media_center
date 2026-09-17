"""Application-owned streaming proxy."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from starlette.background import BackgroundTask
from starlette.responses import StreamingResponse

from media_center.dependencies import get_torrent_backend
from media_center.torrents import (
    TorrentBackend,
    TorrentBackendError,
    TorrentBackendUnavailable,
    TorrentHandle,
)

router = APIRouter(tags=["playback"])

FORWARDED_RESPONSE_HEADERS = frozenset(
    {
        "accept-ranges",
        "cache-control",
        "content-disposition",
        "content-length",
        "content-range",
        "content-type",
        "etag",
        "last-modified",
        "transfermode.dlna.org",
    }
)


@router.api_route(
    "/play/{info_hash}/{file_index}",
    methods=["GET", "HEAD"],
    include_in_schema=False,
)
async def stream_torrent(
    info_hash: str,
    file_index: int,
    request: Request,
    backend: Annotated[TorrentBackend, Depends(get_torrent_backend)],
) -> Response:
    try:
        stream = await backend.open_stream(
            TorrentHandle(info_hash=info_hash.lower()),
            file_index,
            request.method,
            request.headers,
        )
    except TorrentBackendUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Torrent stream is unavailable.",
        ) from exc
    except TorrentBackendError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Torrent service returned an invalid response.",
        ) from exc

    headers = {
        name: value
        for name, value in stream.headers.items()
        if name.lower() in FORWARDED_RESPONSE_HEADERS
    }
    if request.method == "HEAD":
        await stream.close()
        return Response(status_code=stream.status_code, headers=headers)
    return StreamingResponse(
        stream.body,
        status_code=stream.status_code,
        headers=headers,
        background=BackgroundTask(stream.close),
    )
