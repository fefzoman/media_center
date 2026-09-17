"""Environment configuration for the media-center services."""

import os

from pydantic import BaseModel, Field


class Settings(BaseModel):
    media_center_host: str = "0.0.0.0"
    media_center_port: int = Field(default=8000, ge=1, le=65535)
    torrserver_base_url: str = "http://torrserver:8090"
    database_url: str = "sqlite:////data/media-center.db"
    tv_base_url: str = "http://192.168.1.50"
    default_client_id: str = "lg-living-room"
    torrent_cache_mb: int = Field(default=1024, gt=0)
    torrent_use_disk: bool = False
    torrserver_request_timeout_seconds: float = Field(default=10.0, gt=0)
    torrserver_metadata_timeout_seconds: float = Field(default=120.0, gt=0)
    torrserver_poll_interval_seconds: float = Field(default=1.0, gt=0)
    enable_debug_endpoint: bool = True

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls.model_validate(
            {
                name: os.environ[name.upper()]
                for name in cls.model_fields
                if name.upper() in os.environ
            }
        )
