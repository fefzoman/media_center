"""Engine-independent torrent types and interface."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from dataclasses import dataclass


class TorrentBackendError(RuntimeError):
    """Base error for torrent engine operations."""


class TorrentBackendUnavailable(TorrentBackendError):
    """The torrent engine could not be reached."""


class TorrentProtocolError(TorrentBackendError):
    """The torrent engine returned an invalid or unsuccessful response."""


class TorrentMetadataTimeout(TorrentBackendError):
    """Torrent metadata did not become available before the deadline."""


@dataclass(frozen=True, slots=True)
class TorrentHandle:
    info_hash: str


@dataclass(frozen=True, slots=True)
class TorrentFile:
    index: int
    path: str
    length: int


@dataclass(slots=True)
class TorrentStream:
    status_code: int
    headers: Mapping[str, str]
    body: AsyncIterator[bytes]
    close: Callable[[], Awaitable[None]]


class TorrentBackend(ABC):
    @abstractmethod
    async def ensure_source(self, torrent_uri: str) -> TorrentHandle:
        """Register an ephemeral source and wait until metadata is available."""

    @abstractmethod
    async def list_files(self, handle: TorrentHandle) -> list[TorrentFile]:
        """Return files from torrent metadata."""

    @abstractmethod
    async def get_stream_url(self, handle: TorrentHandle, file_index: int) -> str:
        """Return the application-owned URL for the selected stream."""

    @abstractmethod
    async def open_stream(
        self,
        handle: TorrentHandle,
        file_index: int,
        request_method: str,
        request_headers: Mapping[str, str],
    ) -> TorrentStream:
        """Open the engine stream while keeping its response lazy."""

    @abstractmethod
    async def remove_source(self, handle: TorrentHandle) -> None:
        """Drop an ephemeral torrent and its RAM cache."""

    @abstractmethod
    async def health(self) -> bool:
        """Return whether the engine answers its liveness endpoint."""

    @abstractmethod
    async def configure(self, cache_mb: int, use_disk: bool) -> None:
        """Apply and verify required cache settings."""
