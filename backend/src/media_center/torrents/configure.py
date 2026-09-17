"""Apply required TorrServer cache settings before the backend starts."""

import asyncio

import httpx

from media_center.config import Settings
from media_center.torrents.torrserver import TorrServerBackend


async def configure() -> None:
    settings = Settings.from_environment()
    timeout = httpx.Timeout(
        settings.torrserver_request_timeout_seconds,
        connect=settings.torrserver_request_timeout_seconds,
    )
    async with httpx.AsyncClient(
        base_url=settings.torrserver_base_url.rstrip("/"), timeout=timeout
    ) as client:
        backend = TorrServerBackend(client)
        await backend.configure(settings.torrent_cache_mb, settings.torrent_use_disk)


if __name__ == "__main__":
    asyncio.run(configure())
