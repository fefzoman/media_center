# Phase 1 — TorrServer integration

## Purpose

Phase 1 added progressive BitTorrent playback behind an application-owned
interface. Its purpose was to prove the complete path from an authorized magnet
or `.torrent` source to a same-origin HTTP video stream without requiring a
complete movie download or persistent movie storage.

## What was delivered

### TorrServer-LT-gst service

- Added a custom Debian-based image that downloads the official
  `TorrServer-LT-gst` binary for amd64 or arm64.
- Pinned the release and SHA-256 checksums so builds fail if the downloaded
  binary does not match the expected artifact.
- Installed the GStreamer and ffmpeg runtime needed by the `-gst` build.
- Published TCP and UDP port 32000 for BitTorrent peer traffic while keeping
  the TorrServer administrative HTTP port private to Compose.

This gives the Dell responsibility for peer networking, piece selection,
buffering, seeking support, and future media conversion.

### Verified RAM-only configuration

- Added a one-shot `torrserver-init` service that runs before FastAPI.
- Verified that the engine contains built-in GStreamer support.
- Applied and read back a configurable cache size, defaulting to 1 GB.
- Applied `UseDisk=false` by default.
- Persisted only TorrServer configuration; no movie-cache volume was added.

Startup fails when these required settings cannot be verified. This prevents a
deployment from silently writing movie data to disk or running without the
planned conversion capability.

### Torrent abstraction and adapter

- Added the engine-independent `TorrentBackend` interface and typed torrent
  handle, file, and stream models.
- Added `TorrServerBackend` as the only module that calls TorrServer-specific
  endpoints.
- Implemented ephemeral source registration, metadata polling, file listing,
  stream URL generation, lazy stream opening, source removal, health checks,
  and engine configuration.
- Added explicit network and metadata timeouts.

FastAPI routes depend on the abstraction rather than TorrServer request shapes,
which leaves room to change the engine or test routes without a live torrent
service.

### Media-file selection

- Added supported video-extension filtering.
- Excluded files whose basename contains `sample`.
- Selected the largest remaining video by default.
- Supported an explicit preferred file index for later playback flows.

This resolves common multi-file torrents predictably while keeping the policy
independent of TorrServer.

### Development resolver and playback proxy

- Added the non-production `POST /api/v1/debug/play` endpoint.
- Accepted an authorized magnet URI or `.torrent` URL.
- Returned the selected filename, ready status, and a same-origin stream URL.
- Added `GET` and `HEAD /play/{info_hash}/{file_index}`.
- Forwarded range and conditional request headers to TorrServer.
- Preserved playback headers including content type, content length,
  `Accept-Ranges`, and `Content-Range`.
- Disabled nginx response buffering for the playback path.
- Added useful HTTP responses for unavailable services, metadata timeouts,
  missing video files, and invalid engine responses.

The browser never needs the TorrServer address or the original source URI. The
same-origin URL also avoids exposing the engine's administrative interface to
the LAN.

### Health, configuration, and documentation

- Extended `/api/v1/health` to probe TorrServer and report `ok` or `degraded`.
- Added environment settings for the engine version, request and metadata
  timeouts, poll interval, peer port, cache mode, and debug endpoint.
- Updated the smoke check, API documentation, architecture, operations guide,
  and root README for the working Phase 1 flow.

## Validation performed

- Ran Ruff linting and formatting checks successfully.
- Ran 16 pytest tests covering configuration, health behavior, response
  parsing, file selection, debug resolution, GStreamer/cache verification, and
  range-header forwarding.
- Built the pinned TorrServer-LT-gst image and started the complete Compose
  dependency chain successfully.
- Verified effective engine settings:
  `CacheSize=1073741824`, `UseDisk=false`, and GStreamer built in.
- Passed nginx syntax checking and the live stack smoke checks.
- Resolved an authorized Big Buck Bunny MP4 test torrent.
- Requested bytes `0-1048575` through nginx, FastAPI, and TorrServer and received
  HTTP `206 Partial Content`, the correct `Content-Range`, exactly 1 MiB, and a
  valid MP4 payload from a 43 MB source.

The range test demonstrated progressive delivery before the complete video was
downloaded. Temporary validation torrents and engine registrations were removed
after the test.

## Result and next-phase boundary

At the end of Phase 1, the backend can register an authorized torrent, identify
its primary video, and expose a progressive same-origin stream. Actual playback
still needs validation on the target LG model. Catalog records, media-source
storage, poster browsing, and normal user-facing playback orchestration belong
to Phase 2 and later phases.
