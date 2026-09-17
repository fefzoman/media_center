"""Non-production endpoint for validating the Phase 1 torrent pipeline."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from media_center.config import Settings
from media_center.dependencies import get_settings, get_torrent_backend
from media_center.torrents import (
    NoPlayableMediaError,
    TorrentBackend,
    TorrentBackendError,
    TorrentBackendUnavailable,
    TorrentMetadataTimeout,
    select_media_file,
)

router = APIRouter(prefix="/debug", tags=["debug"])


class DebugPlayRequest(BaseModel):
    torrent_uri: str = Field(min_length=1)


class DebugPlayResponse(BaseModel):
    stream_url: str
    file: str
    status: Literal["ready"] = "ready"


@router.post(
    "/play",
    response_model=DebugPlayResponse,
    summary="Resolve an authorized test torrent (development only)",
)
async def debug_play(
    request: DebugPlayRequest,
    backend: Annotated[TorrentBackend, Depends(get_torrent_backend)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> DebugPlayResponse:
    if not settings.enable_debug_endpoint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    try:
        handle = await backend.ensure_source(request.torrent_uri)
        torrent_file = select_media_file(await backend.list_files(handle))
        stream_url = await backend.get_stream_url(handle, torrent_file.index)
    except TorrentBackendUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Torrent service is unavailable.",
        ) from exc
    except TorrentMetadataTimeout as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Torrent metadata did not become available before the timeout.",
        ) from exc
    except NoPlayableMediaError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    except TorrentBackendError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Torrent service returned an invalid response.",
        ) from exc
    return DebugPlayResponse(stream_url=stream_url, file=torrent_file.path)
