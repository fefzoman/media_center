# API — Phase 0

`GET /api/v1/health` returns HTTP 200 with `application/json`:

```json
{"status":"ok","torrserver":"not_configured"}
```

This endpoint reports backend liveness and makes no external network calls.
`not_configured` explicitly means that Phase 1's torrent integration is absent.
It must not be interpreted as engine readiness. Phase 1 will add an actual
dependency probe and document the resulting health/degraded semantics.

Interactive documentation is at `/api/docs`; OpenAPI is at `/api/openapi.json`.
The generated OpenAPI schema describes the implemented endpoint only.

Catalog, start/stop playback, progress and Continue Watching endpoints in
`IMPLEMENTATION_PLAN.md` are future contracts and are not implemented here.
nginx reserves `/play/` with HTTP 501 until stream routing exists.
