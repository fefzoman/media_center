"""Select the primary playable file without engine-specific knowledge."""

from pathlib import PurePosixPath

from media_center.torrents.base import TorrentFile

VIDEO_EXTENSIONS = frozenset({".mkv", ".mp4", ".m4v", ".avi", ".webm", ".ts", ".m2ts"})


class NoPlayableMediaError(ValueError):
    """A torrent contains no non-sample video file."""


def select_media_file(
    files: list[TorrentFile], preferred_file_index: int | None = None
) -> TorrentFile:
    if preferred_file_index is not None:
        for torrent_file in files:
            if torrent_file.index == preferred_file_index:
                return torrent_file
        raise NoPlayableMediaError("The preferred file index does not exist.")

    candidates = [
        torrent_file
        for torrent_file in files
        if PurePosixPath(torrent_file.path).suffix.lower() in VIDEO_EXTENSIONS
        and "sample" not in PurePosixPath(torrent_file.path).name.lower()
    ]
    if not candidates:
        raise NoPlayableMediaError("The torrent contains no playable video file.")
    return max(candidates, key=lambda torrent_file: torrent_file.length)
