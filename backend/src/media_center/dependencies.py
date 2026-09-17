"""FastAPI dependencies for application-owned resources."""

from fastapi import Request

from media_center.config import Settings
from media_center.torrents import TorrentBackend


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_torrent_backend(request: Request) -> TorrentBackend:
    return request.app.state.torrent_backend
