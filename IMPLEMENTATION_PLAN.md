# LG webOS Torrent Streaming Media Center — Implementation Plan

## 1. Goal

Build a self-hosted media center that provides a streaming-service-like experience on an LG webOS TV.

The user experience should be:

1. Open **My Media** on the LG TV.
2. Browse a poster-based movie catalog.
3. Select a title.
4. Press **Play**.
5. Playback begins after a short buffer.
6. The source media is streamed progressively from BitTorrent.
7. The complete movie is **not pre-downloaded** and is **not retained as a persistent movie file**.
8. Seeking should work by reprioritizing torrent pieces around the target position.
9. Playback state should support pause/resume and "Continue Watching".

Use this only with media the operator is authorized to access/distribute via BitTorrent.

---

## 2. Target Hardware

### Media server

Dell Vostro:

- CPU: AMD Ryzen 5 3450U
- RAM: 16 GB
- SSD: 256 GB
- Network: Gigabit Ethernet preferred
- OS: Debian 13

The Dell performs all heavy work:

- torrent networking
- piece prioritization
- RAM caching
- optional remux/transcoding
- HLS generation
- catalog/API services
- web UI hosting
- playback-state persistence

### TV

LG Smart TV running webOS.

Do **not** depend on Media Station X.

The TV should initially use its built-in browser for development/testing.

The production client should be a small custom webOS application installed through LG Developer Mode.

The actual UI should be hosted by the Dell whenever practical so the TV application remains very small.

---

## 3. High-Level Architecture

```text
                         INTERNET
                            |
                    BitTorrent peers
                            |
                            v
+-------------------------------------------------------------+
|                      DELL VOSTRO                            |
|                                                             |
|  +-----------------------+                                  |
|  | TorrServer-LT-gst     |                                  |
|  |                       |                                  |
|  | - libtorrent          |                                  |
|  | - piece priority      |                                  |
|  | - RAM cache           |                                  |
|  | - HTTP stream         |                                  |
|  | - HLS fallback        |                                  |
|  | - optional remux      |                                  |
|  | - optional transcode  |                                  |
|  +-----------+-----------+                                  |
|              |                                              |
|              v                                              |
|  +-----------------------+                                  |
|  | Playback Service      |                                  |
|  |                       |                                  |
|  | - start playback      |                                  |
|  | - resolve file        |                                  |
|  | - choose direct/HLS   |                                  |
|  | - progress state      |                                  |
|  +-----------+-----------+                                  |
|              |                                              |
|  +-----------v-----------+        +----------------------+  |
|  | Catalog API           |<------>| SQLite/PostgreSQL    |  |
|  +-----------+-----------+        +----------------------+  |
|              |                                              |
|  +-----------v-----------+                                  |
|  | TV Web Frontend       |                                  |
|  | nginx/static server   |                                  |
|  +-----------+-----------+                                  |
|              |                                              |
+--------------+----------------------------------------------+
               |
          HTTP / HLS
               |
               v
+-------------------------------------------------------------+
|                        LG webOS TV                          |
|                                                             |
|  Phase 1: built-in browser                                  |
|                                                             |
|  Phase 2+: custom "My Media" webOS app                      |
|                                                             |
|  - poster UI                                                |
|  - D-pad navigation                                         |
|  - movie details                                            |
|  - HTML5 video player                                       |
|  - play/pause/seek/back                                     |
+-------------------------------------------------------------+
```

---

## 4. Core Design Decisions

### 4.1 Torrent engine

Use:

```text
TorrServer-LT-gst
```

The torrent engine must run on the Dell, not on the TV.

Required behavior:

- accept torrent/magnet metadata for authorized media
- begin fetching pieces required for playback
- prioritize pieces near the current playback position
- expose playable HTTP stream URLs
- support seeking
- allow HLS/remux/transcoding fallback where needed

Do not implement a torrent engine from scratch.

---

### 4.2 No persistent movie download

The application must not require a complete movie file before playback.

Preferred configuration:

```text
UseDisk = false
CacheSize ~= 1024 MB
```

Initial target:

```text
torrent RAM cache: 1 GB
```

The SSD is for:

- OS
- application code
- metadata
- database
- logs
- configuration
- temporary operational data

It is not intended to hold a permanent downloaded movie library.

---

### 4.3 Playback strategy

Prefer the lowest-cost playback path.

#### Path A — Direct Play

Use when the LG TV supports the original media container/codecs.

```text
torrent
  |
  v
TorrServer
  |
  v
HTTP stream
  |
  v
LG HTML5 video player
```

This is the preferred path.

---

#### Path B — Remux/audio conversion

Use when video is compatible but the container/audio is not.

Example:

```text
HEVC video  -> copy
DTS/EAC3    -> AAC
container   -> HLS
```

Avoid video re-encoding when possible.

---

#### Path C — Full transcode

Use only when the TV cannot decode the video format.

```text
source video
   |
   v
GStreamer
   |
   +-> H.264 or another TV-compatible format
   +-> AAC
   |
   v
HLS
```

This should be a fallback because it consumes much more CPU.

---

## 5. Repository Layout

Create a monorepo initially.

Suggested structure:

```text
media-center/
|
|-- AGENTS.md
|-- README.md
|-- docker-compose.yml
|-- .env.example
|-- Makefile
|
|-- docs/
|   |-- architecture.md
|   |-- api.md
|   |-- webos.md
|   `-- operations.md
|
|-- backend/
|   |-- pyproject.toml
|   |-- src/
|   |   `-- media_center/
|   |       |-- main.py
|   |       |-- config.py
|   |       |-- api/
|   |       |-- catalog/
|   |       |-- playback/
|   |       |-- torrents/
|   |       |-- metadata/
|   |       `-- persistence/
|   `-- tests/
|
|-- frontend/
|   |-- index.html
|   |-- css/
|   |-- js/
|   `-- assets/
|
|-- webos/
|   |-- appinfo.json
|   |-- index.html
|   |-- app.js
|   `-- icon.png
|
|-- infra/
|   |-- nginx/
|   |   `-- nginx.conf
|   `-- torrserver/
|       `-- README.md
|
`-- scripts/
    |-- bootstrap.sh
    |-- dev.sh
    `-- smoke-test.sh
```

Keep the initial frontend lightweight.

Do not introduce React/Vue/Angular unless there is a demonstrated need.

Older webOS browser engines may have limited JavaScript support.

Prefer:

- plain HTML
- plain CSS
- conservative JavaScript
- minimal dependencies

---

## 6. Backend Technology

Preferred initial stack:

```text
Python 3.12+
FastAPI
Pydantic
SQLAlchemy
SQLite
httpx
```

SQLite is sufficient for the first implementation.

The data model should allow migration to PostgreSQL later without redesigning the API.

Use asynchronous HTTP calls where appropriate.

---

## 7. Backend Responsibilities

The backend should own:

- catalog
- title metadata
- media-source records
- playback sessions
- integration with TorrServer
- continue-watching state
- playback progress
- stream selection
- health reporting

The frontend must not call TorrServer directly unless there is a strong reason.

Preferred flow:

```text
LG client
   |
   v
Backend API
   |
   v
TorrServer
```

This provides one stable application API and keeps torrent-specific details out of the TV UI.

---

## 8. Initial Data Model

### Movie

```text
id
title
original_title
year
description
poster_url
backdrop_url
runtime_seconds
created_at
updated_at
```

### MediaSource

```text
id
movie_id
source_type
torrent_uri
info_hash
preferred_file_index
created_at
```

`source_type` initially:

```text
torrent
```

Do not expose raw source information in normal catalog API responses unless required.

### PlaybackProgress

```text
id
movie_id
client_id
position_seconds
duration_seconds
completed
updated_at
```

### PlaybackSession

```text
id
movie_id
media_source_id
client_id
status
stream_mode
stream_url
started_at
last_seen_at
```

Possible `stream_mode` values:

```text
direct
hls_remux
hls_transcode
```

---

## 9. API Contract

Base path:

```text
/api/v1
```

### Health

```http
GET /api/v1/health
```

Example:

```json
{
  "status": "ok",
  "torrserver": "ok"
}
```

---

### List movies

```http
GET /api/v1/movies
```

Response:

```json
[
  {
    "id": "movie_001",
    "title": "Example Movie",
    "year": 2025,
    "poster_url": "/assets/posters/movie_001.jpg",
    "progress": 0.42
  }
]
```

---

### Movie details

```http
GET /api/v1/movies/{movie_id}
```

---

### Start playback

```http
POST /api/v1/movies/{movie_id}/play
```

Request:

```json
{
  "client_id": "lg-living-room",
  "capabilities": {
    "h264": true,
    "hevc": true,
    "aac": true,
    "hls": true
  }
}
```

Response:

```json
{
  "session_id": "session_123",
  "mode": "direct",
  "url": "http://SERVER/play/session_123",
  "resume_position_seconds": 1830
}
```

The backend must:

1. identify the configured torrent source
2. register/activate it in TorrServer
3. identify the media file to play
4. determine the playback mode
5. return the appropriate stream URL

---

### Update playback progress

```http
PUT /api/v1/playback/{session_id}/progress
```

Request:

```json
{
  "position_seconds": 1925,
  "duration_seconds": 7200
}
```

The client should update progress periodically, for example every 10-30 seconds.

---

### Stop playback

```http
POST /api/v1/playback/{session_id}/stop
```

This should allow cleanup of ephemeral playback resources.

---

### Continue watching

```http
GET /api/v1/continue-watching
```

---

## 10. TorrServer Integration Layer

Create a dedicated abstraction:

```text
backend/src/media_center/torrents/
```

Suggested interface:

```python
class TorrentBackend:
    async def ensure_source(self, torrent_uri: str) -> TorrentHandle:
        ...

    async def list_files(self, handle: TorrentHandle) -> list[TorrentFile]:
        ...

    async def get_stream_url(
        self,
        handle: TorrentHandle,
        file_index: int,
    ) -> str:
        ...

    async def remove_source(self, handle: TorrentHandle) -> None:
        ...

    async def health(self) -> bool:
        ...
```

Implement:

```text
TorrServerBackend
```

Do not allow TorrServer-specific HTTP calls throughout the application.

All TorrServer API interactions must pass through this adapter.

This will make it possible to replace or upgrade the torrent backend later.

---

## 11. Media File Selection

A torrent may contain:

```text
movie.mkv
sample.mkv
poster.jpg
readme.txt
```

The application must select the main playable media file.

Initial heuristic:

1. filter video files
2. exclude names containing `sample`
3. choose the largest video file

Supported initial extensions:

```text
.mkv
.mp4
.m4v
.avi
.webm
.ts
.m2ts
```

Allow `preferred_file_index` in the database to override automatic selection.

---

## 12. TV Frontend

The frontend is designed for a remote control, not mouse/keyboard use.

Required controls:

```text
Up
Down
Left
Right
OK / Enter
Back
Play
Pause
Seek forward
Seek backward
```

The focus state must always be visible.

Do not depend on hover interactions.

---

## 13. Initial UI

Home page:

```text
+-----------------------------------------------------------+
| MY MEDIA                                                  |
|                                                           |
| Continue Watching                                         |
|                                                           |
| [poster]  [poster]  [poster]  [poster]                    |
|                                                           |
| Movies                                                    |
|                                                           |
| [poster]  [poster]  [poster]  [poster]                    |
| [poster]  [poster]  [poster]  [poster]                    |
+-----------------------------------------------------------+
```

Movie page:

```text
+-----------------------------------------------------------+
|                                                           |
|   [POSTER]    Movie Title                                 |
|               2025 - 2h 04m                              |
|                                                           |
|               Description...                              |
|                                                           |
|               [ PLAY ]                                    |
|                                                           |
+-----------------------------------------------------------+
```

Player:

```text
+-----------------------------------------------------------+
|                                                           |
|                        VIDEO                              |
|                                                           |
|                                                           |
|  00:31:42  ========================------  02:00:00        |
|                                                           |
|                     Pause / Seek                          |
+-----------------------------------------------------------+
```

---

## 14. HTML5 Player

Initial implementation:

```html
<video
  id="player"
  autoplay
  controls
  playsinline>
</video>
```

However, eventually replace browser-native controls with TV-friendly custom controls.

Player responsibilities:

- load playback URL
- start playback
- resume from saved position
- catch playback errors
- send progress updates
- support seek
- send stop event where possible
- restore focus when leaving playback

---

## 15. Browser-First Development

Before creating the webOS package, the frontend must work from:

```text
http://SERVER_IP/tv/
```

Test directly in the LG webOS built-in browser.

This is Phase 1.

Do not begin with LG packaging.

First prove:

```text
catalog
   ->
select movie
   ->
start torrent
   ->
buffer
   ->
play
   ->
seek
   ->
resume
```

---

## 16. webOS Application

Once browser playback works, create a small native webOS web application.

The webOS app should contain as little logic as possible.

Preferred responsibility:

```text
launch My Media
   |
   v
load application UI from Dell
```

Possible structure:

```text
webos/
|-- appinfo.json
|-- index.html
|-- app.js
`-- icon.png
```

Example concept:

```json
{
  "id": "com.home.mymedia",
  "version": "1.0.0",
  "vendor": "Home",
  "type": "web",
  "main": "index.html",
  "title": "My Media",
  "icon": "icon.png"
}
```

The launcher should open:

```text
http://SERVER_IP/tv/
```

If hosted-app restrictions on the specific TV/webOS generation prevent this approach, package the same frontend inside the IPK while keeping all backend APIs on the Dell.

---

## 17. Networking

Assign the Dell a stable LAN IP.

Example:

```text
192.168.1.50
```

Preferred:

```text
router DHCP reservation
```

rather than manually configuring the OS unless necessary.

Expected local endpoints:

```text
http://192.168.1.50/
http://192.168.1.50/tv/
http://192.168.1.50/api/v1/
```

TorrServer should not need to be exposed directly to the TV or Internet.

---

## 18. Reverse Proxy

Use nginx.

External layout:

```text
/tv/        -> frontend static files
/api/       -> FastAPI
/play/      -> playback proxy/stream endpoint
```

TorrServer should remain on an internal/local port.

Example:

```text
127.0.0.1:8090 -> TorrServer
127.0.0.1:8000 -> FastAPI
0.0.0.0:80     -> nginx
```

---

## 19. Docker

Use Docker Compose for the initial server deployment.

Expected services:

```text
nginx
backend
torrserver
```

Optional later:

```text
postgres
redis
```

Do not introduce Redis during the first milestone unless required.

Conceptual Compose layout:

```yaml
services:
  torrserver:
    ...

  backend:
    ...

  nginx:
    ...
```

For TorrServer configuration that requires host networking or special networking behavior, document the reason explicitly.

---

## 20. Configuration

All environment-dependent values must use environment variables.

Create:

```text
.env.example
```

Initial variables:

```text
MEDIA_CENTER_HOST=0.0.0.0
MEDIA_CENTER_PORT=8000

TORRSERVER_BASE_URL=http://torrserver:8090

DATABASE_URL=sqlite:///data/media-center.db

TV_BASE_URL=http://192.168.1.50
DEFAULT_CLIENT_ID=lg-living-room

TORRENT_CACHE_MB=1024
TORRENT_USE_DISK=false
```

Never commit credentials.

---

## 21. Observability

At minimum log:

```text
playback_session_created
torrent_registered
torrent_ready
stream_started
stream_mode
playback_seek
playback_stopped
playback_error
torrserver_error
```

Include:

```text
session_id
movie_id
client_id
```

where relevant.

Avoid logging complete sensitive URLs or secrets.

---

## 22. Failure Handling

The frontend must display useful errors rather than hanging indefinitely.

Examples:

### Torrent has no peers

```text
Unable to start playback.
No peers are currently available.
```

### Buffering timeout

```text
Stream is taking too long to start.
Retry?
```

### Unsupported playback format

Backend should attempt:

```text
direct
  ->
HLS remux
  ->
HLS transcode
```

before returning an unsupported-media error.

### Backend unavailable

TV frontend:

```text
Media server unavailable.
```

---

## 23. Playback Startup State Machine

Implement playback initiation explicitly.

```text
REQUESTED
   |
   v
SOURCE_REGISTERING
   |
   v
FILE_RESOLVING
   |
   v
BUFFERING
   |
   v
READY
   |
   v
PLAYING
```

Failure terminal state:

```text
ERROR
```

Optional stop state:

```text
STOPPED
```

Do not bury this state inside UI logic.

The backend should be authoritative for session state.

---

## 24. Continue Watching

A movie should appear in Continue Watching when:

```text
progress > 5%
AND
progress < 90%
```

A movie can be marked completed when:

```text
progress >= 90%
```

These thresholds should be configurable later.

---

## 25. Security Scope

Initial deployment is LAN-only.

Do not expose torrent or playback services directly to the public Internet.

Initial assumptions:

```text
trusted home LAN
single user
no authentication required
```

Keep the API structured so authentication can be added later.

---

## 26. Development Phases

# Phase 0 — Repository bootstrap

Create:

- repository structure
- AGENTS.md
- README.md
- backend skeleton
- frontend skeleton
- Docker Compose
- nginx configuration
- `.env.example`
- unit-test framework
- lint/format configuration

Acceptance:

```text
docker compose up
```

starts the stack and:

```http
GET /api/v1/health
```

returns `200`.

---

# Phase 1 — TorrServer integration

Implement:

- TorrServer container/service
- health check
- torrent adapter
- add/register source
- list torrent files
- select primary media file
- obtain stream URL

No catalog UI is required yet.

Create a developer endpoint if necessary:

```http
POST /api/v1/debug/play
```

Input:

```json
{
  "torrent_uri": "..."
}
```

Output:

```json
{
  "stream_url": "...",
  "file": "...",
  "status": "ready"
}
```

This debug endpoint must be clearly marked non-production.

Acceptance:

Given an authorized test torrent containing video:

1. backend registers torrent
2. backend identifies media file
3. backend returns stream URL
4. video can be opened from a desktop browser
5. playback starts without complete pre-download

---

# Phase 2 — Minimal catalog

Implement:

- Movie table
- MediaSource table
- seed data
- `GET /movies`
- `GET /movies/{id}`
- `POST /movies/{id}/play`

Acceptance:

A catalog movie can be started through movie ID without passing a magnet URI from the frontend.

---

# Phase 3 — TV browser UI

Implement:

- home screen
- movie cards
- details page
- Play button
- HTML5 player
- keyboard/D-pad navigation
- Back behavior
- loading/buffering state
- playback error screen

Acceptance on LG browser:

```text
open /tv/
browse
select
play
pause
seek
back
```

all function with the LG remote.

---

# Phase 4 — Playback progress

Implement:

- PlaybackSession persistence
- progress heartbeat
- resume position
- Continue Watching

Acceptance:

1. play a movie
2. stop after several minutes
3. reopen home page
4. movie appears in Continue Watching
5. resume starts close to previous position

---

# Phase 5 — Playback compatibility

Implement playback capability negotiation.

Add:

```text
direct
hls_remux
hls_transcode
```

modes.

Backend should choose the cheapest compatible mode.

Acceptance:

- compatible source uses Direct Play
- incompatible audio can be converted without re-encoding video
- unsupported video can fall back to transcode where practical

---

# Phase 6 — webOS package

Create:

```text
webos/
```

Package application as IPK.

It should:

- appear as "My Media"
- launch from LG Home
- load the TV UI
- support remote controls
- enter/exit playback correctly

Acceptance:

The normal user flow no longer requires opening the LG browser manually.

---

# Phase 7 — Hardening

Add:

- better retry behavior
- startup checks
- container restart policies
- persistent application database
- log rotation
- graceful torrent/session cleanup
- network timeout handling
- health monitoring
- backup instructions

---

## 27. Non-Goals for MVP

Do not build these during the first implementation:

- user accounts
- recommendations engine
- cloud deployment
- public Internet access
- multi-node torrent cluster
- mobile apps
- full Plex/Jellyfin integration
- sophisticated search engine
- Kubernetes
- Redis
- PostgreSQL unless SQLite becomes limiting
- custom BitTorrent implementation

Keep the first usable version small.

---

## 28. Testing Strategy

### Backend unit tests

Cover:

- file-selection heuristic
- playback-mode selection
- progress calculations
- session state transitions
- TorrServer response parsing

### Integration tests

Cover:

```text
backend -> TorrServer
backend -> database
nginx -> backend
```

### Manual LG tests

Maintain a compatibility matrix:

```text
Codec     Container    Audio      Direct?   HLS?   Notes
H.264     MP4          AAC
H.264     MKV          AC3
HEVC      MKV          AAC
HEVC      MKV          EAC3
HEVC      MKV          DTS
```

Do not assume codec support solely from generic webOS documentation.

Verify on the actual TV.

---

## 29. Performance Targets

Initial targets:

### Startup

From pressing Play to first rendered video:

```text
target: <= 10 seconds under healthy swarm conditions
```

This depends on torrent peer availability and is therefore not guaranteed.

### Local network

Preferred:

```text
Dell -> router: Gigabit Ethernet
```

### Torrent cache

Start with:

```text
1 GB RAM
```

Make configurable.

### CPU

Direct Play should consume minimal CPU.

Remux/audio conversion should remain light.

Full video transcoding is allowed to consume significant CPU but must not be the default path.

---

## 30. Coding Principles

- Keep torrent-specific logic behind an adapter.
- Keep LG/webOS-specific code out of the backend.
- Prefer simple implementations over framework-heavy abstractions.
- Make all network calls timeout explicitly.
- Use typed Python.
- Use structured logging.
- Keep APIs versioned under `/api/v1`.
- Do not mix persistence models directly into API handlers.
- Add tests for every non-trivial selection/state algorithm.
- Avoid premature distributed-system components.
- Keep browser compatibility conservative.

---

## 31. Suggested AGENTS.md

Create the following repository instructions:

```md
# Repository Instructions

## Project

This repository implements a self-hosted media center for LG webOS.

The Dell server handles torrent-backed progressive playback using
TorrServer-LT-gst. The TV is a thin HTTP/HLS client.

## Architecture Rules

- TorrServer-specific calls must be isolated behind the torrent backend adapter.
- The frontend must never contain torrent credentials or backend implementation details.
- Prefer Direct Play over remuxing.
- Prefer remuxing/audio conversion over full video transcoding.
- Do not require complete movie downloads before playback.
- Persistent movie storage is outside the MVP.
- Keep the frontend compatible with older webOS browser engines.
- Keep the initial deployment LAN-only.

## Backend

- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite initially
- pytest
- ruff

Use type hints.

All outbound HTTP calls must use explicit timeouts.

## Frontend

Use conservative HTML/CSS/JavaScript.

Do not introduce React, Vue, Angular, or a build pipeline unless there is
a concrete requirement that plain JavaScript cannot reasonably satisfy.

The TV UI must be fully usable with D-pad navigation.

## Tests

Before completing backend changes run:

    ruff check .
    pytest

Add unit tests for business logic.

## Security

Never commit secrets.

Do not expose TorrServer directly to the public Internet.

Assume LAN-only operation for the MVP.

## Scope

Implement phases in IMPLEMENTATION_PLAN.md sequentially.

Do not skip directly to webOS packaging before browser playback works.
```

---

## 32. First Codex Task

After placing this file in the repository as:

```text
IMPLEMENTATION_PLAN.md
```

give Codex this task:

```text
Read IMPLEMENTATION_PLAN.md completely.

Implement Phase 0 only.

Create the repository skeleton, AGENTS.md, Docker Compose configuration,
FastAPI backend with /api/v1/health, minimal static TV frontend, nginx
reverse proxy, .env.example, linting, pytest configuration, Makefile, and
basic documentation.

Do not implement torrent playback yet.

Run the available tests/lint checks and fix failures.

At the end, report:
1. files created,
2. architectural decisions made,
3. commands to run the stack,
4. test/lint results,
5. anything that blocks Phase 1.
```

After Phase 0 is verified, proceed with:

```text
Implement Phase 1 from IMPLEMENTATION_PLAN.md.

Integrate TorrServer-LT-gst through the TorrentBackend abstraction.
Do not leak TorrServer-specific API calls into FastAPI route handlers.

Use an authorized test torrent for validation.

Add tests for response parsing and media-file selection.

Do not implement the full catalog UI yet.
```

---

## 33. Definition of MVP Complete

The MVP is complete when this flow works on the actual LG TV:

```text
LG Home / browser
      |
      v
My Media
      |
      v
movie catalog
      |
      v
movie details
      |
      v
PLAY
      |
      v
backend activates torrent
      |
      v
short buffer
      |
      v
video starts
      |
      +--> pause
      +--> resume
      +--> seek
      |
      v
exit
      |
      v
progress saved
      |
      v
Continue Watching
```

And the following remains true:

```text
No complete movie pre-download is required.
No permanent movie library is required on the Dell SSD.
```
