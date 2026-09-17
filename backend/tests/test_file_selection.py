import pytest

from media_center.torrents import (
    NoPlayableMediaError,
    TorrentFile,
    select_media_file,
)


def test_selects_largest_non_sample_video_case_insensitively() -> None:
    files = [
        TorrentFile(index=1, path="Movie/sample.mkv", length=50_000_000),
        TorrentFile(index=2, path="Movie/readme.txt", length=100),
        TorrentFile(index=3, path="Movie/feature.MP4", length=900_000_000),
        TorrentFile(index=4, path="Movie/featurette.mkv", length=100_000_000),
    ]

    assert select_media_file(files).index == 3


def test_preferred_index_overrides_extension_heuristic() -> None:
    files = [
        TorrentFile(index=1, path="movie.mkv", length=900),
        TorrentFile(index=2, path="alternate.unknown", length=100),
    ]

    assert select_media_file(files, preferred_file_index=2).index == 2


def test_rejects_torrent_without_playable_media() -> None:
    files = [
        TorrentFile(index=1, path="sample.mkv", length=900),
        TorrentFile(index=2, path="poster.jpg", length=100),
    ]

    with pytest.raises(NoPlayableMediaError):
        select_media_file(files)
