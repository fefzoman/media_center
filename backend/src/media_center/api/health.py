"""Application and TorrServer health."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from media_center.dependencies import get_torrent_backend
from media_center.torrents import TorrentBackend

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    torrserver: Literal["ok", "unavailable"]


@router.get("/health", response_model=HealthResponse)
async def health(
    backend: Annotated[TorrentBackend, Depends(get_torrent_backend)],
) -> HealthResponse:
    torrserver_ok = await backend.health()
    return HealthResponse(
        status="ok" if torrserver_ok else "degraded",
        torrserver="ok" if torrserver_ok else "unavailable",
    )
