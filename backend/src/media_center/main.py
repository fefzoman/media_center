"""Application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from media_center.api.debug import router as debug_router
from media_center.api.health import router as health_router
from media_center.api.playback import router as playback_router
from media_center.config import Settings
from media_center.torrents import TorrServerBackend


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = Settings.from_environment()
    timeout = httpx.Timeout(
        settings.torrserver_request_timeout_seconds,
        connect=settings.torrserver_request_timeout_seconds,
    )
    async with httpx.AsyncClient(
        base_url=settings.torrserver_base_url.rstrip("/"), timeout=timeout
    ) as client:
        app.state.settings = settings
        app.state.torrent_backend = TorrServerBackend(
            client,
            metadata_timeout_seconds=settings.torrserver_metadata_timeout_seconds,
            poll_interval_seconds=settings.torrserver_poll_interval_seconds,
        )
        yield


app = FastAPI(
    title="My Media",
    version="0.2.0",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)
app.include_router(health_router, prefix="/api/v1")
app.include_router(debug_router, prefix="/api/v1")
app.include_router(playback_router)
