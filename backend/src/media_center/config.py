"""Environment configuration; integrations consume reserved settings in later phases."""

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

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls.model_validate(
            {
                name: os.environ[name.upper()]
                for name in cls.model_fields
                if name.upper() in os.environ
            }
        )
