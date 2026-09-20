from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_database(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Iterator[None]:
    database_path = tmp_path / "media-center.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv(
        "CATALOG_SEED_TORRENT_URI", "https://example.invalid/authorized.torrent"
    )
    yield
