# TorrServer-LT-gst

The Dockerfile builds the Phase 1 torrent engine from Debian 13 slim and the
official `TorrServer-LT-linux-{amd64,arm64}-gst` release binary. The default
release is `MatriX.142.LT-1.1.8`; both supported binaries are pinned by SHA-256
in the Dockerfile. The image also installs the GStreamer plugins and ffmpeg
runtime required by the `-gst` binary.

Compose exposes TCP and UDP port 32000 for peer traffic. Port 8090 remains
internal. Only `/opt/ts/config` is persistent; there is no movie data volume.
The `torrserver-init` service verifies GStreamer support, applies the configured
`CacheSize` and `UseDisk`, reads the settings back, then allows FastAPI to start.

All application calls to the engine live in
`backend/src/media_center/torrents/torrserver.py`. Rebuild after changing
`TORRSERVER_VERSION`; a new version also requires replacing the architecture
checksums. Test changes with an authorized video torrent that has reachable
peers or an HTTP web seed.
