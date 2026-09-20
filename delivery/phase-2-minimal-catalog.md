# Phase 2 — Minimal catalog

## Purpose

Move torrent source selection out of the frontend. A TV client identifies a
movie, while the backend privately resolves its configured media source.

## Delivered

- Added SQLAlchemy 2.x with SQLite persistence on the existing `/data` volume.
- Added separate `Movie` and `MediaSource` models with an enforced one-source
  catalog relationship for this phase.
- Added an idempotent Sintel seed using [WebTorrent's Creative Commons test
  torrent](https://webtorrent.io/intro); operators can replace the seed source
  through environment settings.
- Added `GET /api/v1/movies`, `GET /api/v1/movies/{id}`, and `POST
  /api/v1/movies/{id}/play`.
- Kept source URLs out of catalog and playback responses.
- Reused `TorrentBackend` for activation, file selection, and stream URL
  generation; handlers contain no TorrServer-specific calls.

## Validation

- Catalog tests verify seed data, details, 404 behavior, source redaction, and
  movie-ID playback with no source supplied by the client.
- The stack smoke test verifies catalog APIs through nginx and the seeded poster
  asset.

## Next boundary

Phase 3 builds the TV browser interaction on this API. Physical LG browser and
remote acceptance remain required before Phase 3 can be declared complete.
