# API — Phase 3

`GET /api/v1/health` returns HTTP 200 with `application/json`:

```json
{"status":"ok","torrserver":"ok"}
```

The endpoint probes TorrServer's `/echo` endpoint. When the engine is
unreachable it returns `{"status":"degraded","torrserver":"unavailable"}`.

`POST /api/v1/debug/play` is a non-production Phase 1 resolver. It accepts:

```json
{"torrent_uri":"magnet:?xt=urn:btih:..."}
```

It registers the source without saving it to TorrServer's database, waits for
metadata, excludes sample files, and selects the largest supported video file.
A successful response is:

```json
{
  "stream_url":"/play/0123456789abcdef0123456789abcdef01234567/1",
  "file":"Movie/Movie.mkv",
  "status":"ready"
}
```

The endpoint returns 404 when `ENABLE_DEBUG_ENDPOINT=false`, 422 when the
torrent has no playable video, 503 when TorrServer is unreachable, 504 when
metadata polling exceeds the configured deadline, and 502 for an invalid or
unsuccessful engine response.

`GET /api/v1/movies` returns catalog cards with `id`, `title`, `year`,
`poster_url`, and a Phase 4-ready `progress` value. `GET
/api/v1/movies/{movie_id}` adds description, original title, backdrop and
runtime. Neither response exposes media-source records or torrent URLs.

`POST /api/v1/movies/{movie_id}/play` accepts client capabilities:

```json
{
  "client_id": "tv-browser",
  "capabilities": {"h264": true, "hevc": true, "aac": true, "hls": true}
}
```

The backend resolves the configured MediaSource by movie ID, activates the
torrent through `TorrentBackend`, selects the preferred or largest playable
file, and returns an opaque direct-play URL:

```json
{
  "session_id": "session_...",
  "mode": "direct",
  "url": "/play/0123456789abcdef0123456789abcdef01234567/1",
  "resume_position_seconds": 0
}
```

`GET` and `HEAD /play/{info_hash}/{file_index}` proxy the selected TorrServer
stream without exposing the engine or the original source URI. Request range
headers and relevant response headers such as `Content-Range`, `Content-Length`
and `Content-Type` are preserved. The route is intentionally omitted from the
OpenAPI document because clients receive it as an opaque stream URL.

Interactive documentation is at `/api/docs`; OpenAPI is at `/api/openapi.json`.
The generated OpenAPI schema describes health, catalog and debug routes.

Persistent playback sessions, progress and Continue Watching endpoints remain
Phase 4 contracts.
