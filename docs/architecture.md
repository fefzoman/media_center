# Architecture

Phase 1 request paths:

```text
Desktop/LG browser -> nginx :80 -> /tv/ static HTML/CSS/JS
                               -> /api/ -> FastAPI :8000
                               -> /play/ -> FastAPI -> TorrServer :8090
BitTorrent peers/web seeds <-----------------------> TorrServer :32000
```

nginx is the only published HTTP service. FastAPI and TorrServer stay on the
Compose network. TCP and UDP port 32000 are published only for BitTorrent peer
traffic. nginx waits for backend health, and the backend starts only after a
one-shot initialization service has applied and verified the engine settings.
The browser uses same-origin API and stream URLs, so no CORS configuration is
required.

The backend uses Python 3.12+, FastAPI, Pydantic and an asynchronous shared
httpx client. Environment configuration is validated at startup. The image
runs as a non-root user. The named `/data` volume is reserved for SQLite
metadata; no database is opened in this phase.

`TorrentBackend` is the engine-independent boundary. `TorrServerBackend` is the
only module that calls TorrServer endpoints. Route handlers work with handles,
files and streams from that interface. SQLAlchemy remains deferred until the
catalog needs persistence.

The custom engine image downloads a checksum-pinned upstream
TorrServer-LT-gst binary for amd64 or arm64 and provides its GStreamer runtime.
The initialization job verifies that GStreamer is built in, sets `UseDisk=false`
and applies the configured RAM cache size. Only the small engine configuration
volume is persistent; no movie-cache volume is mounted. Direct HTTP is the
Phase 1 playback path. HLS remux and transcode selection remain later work.

The frontend uses ES5-style JavaScript and XMLHttpRequest, without frameworks,
modules or a build step. The initial page has one focusable action and a bounded
connection check. Full D-pad catalog navigation and video playback arrive in
Phase 3. webOS packaging waits until browser playback is proven on the actual TV.

Key implementation references:

- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/)
- [nginx proxy URI handling](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_pass)
- [Ruff configuration](https://docs.astral.sh/ruff/configuration/)
- [pytest configuration](https://docs.pytest.org/en/stable/reference/customize.html)
- [TorrServer-LT source and releases](https://github.com/trinity-aml/TorrServer-LT)
- [HTTPX async streaming](https://www.python-httpx.org/async/)
- [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/)
