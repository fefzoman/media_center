"""Start the backend using environment-based listener settings."""

import uvicorn

from media_center.config import Settings


def main() -> None:
    settings = Settings.from_environment()
    uvicorn.run(
        "media_center.main:app",
        host=settings.media_center_host,
        port=settings.media_center_port,
    )


if __name__ == "__main__":
    main()
