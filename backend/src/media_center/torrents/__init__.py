"""Torrent backend adapter boundary."""

from media_center.torrents.base import (
    TorrentBackend,
    TorrentBackendError,
    TorrentBackendUnavailable,
    TorrentFile,
    TorrentHandle,
    TorrentMetadataTimeout,
    TorrentProtocolError,
    TorrentStream,
)
from media_center.torrents.selection import NoPlayableMediaError, select_media_file
from media_center.torrents.torrserver import TorrServerBackend

__all__ = [
    "NoPlayableMediaError",
    "TorrentBackend",
    "TorrentBackendError",
    "TorrentBackendUnavailable",
    "TorrentFile",
    "TorrentHandle",
    "TorrentMetadataTimeout",
    "TorrentProtocolError",
    "TorrentStream",
    "TorrServerBackend",
    "select_media_file",
]
