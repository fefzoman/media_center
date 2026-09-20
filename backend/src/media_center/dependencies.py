"""FastAPI dependencies for application-owned resources."""

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy.orm import Session

from media_center.config import Settings
from media_center.persistence import SessionFactory, session_scope
from media_center.torrents import TorrentBackend


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_torrent_backend(request: Request) -> TorrentBackend:
    return request.app.state.torrent_backend


def get_database_session(request: Request) -> Iterator[Session]:
    factory: SessionFactory = request.app.state.session_factory
    yield from session_scope(factory)
