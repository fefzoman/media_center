import pytest
from pydantic import ValidationError

from media_center.config import Settings


def test_environment_settings_are_typed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MEDIA_CENTER_PORT", "9000")
    monkeypatch.setenv("TORRENT_USE_DISK", "false")
    monkeypatch.setenv("TORRENT_CACHE_MB", "2048")
    monkeypatch.setenv("DEFAULT_CLIENT_ID", "test-tv")

    settings = Settings.from_environment()

    assert settings.media_center_port == 9000
    assert settings.torrent_use_disk is False
    assert settings.torrent_cache_mb == 2048
    assert settings.default_client_id == "test-tv"


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("MEDIA_CENTER_PORT", "0"),
        ("MEDIA_CENTER_PORT", "65536"),
        ("TORRENT_CACHE_MB", "-1"),
        ("TORRENT_USE_DISK", "sometimes"),
    ],
)
def test_invalid_configuration_fails_early(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(ValidationError):
        Settings.from_environment()
