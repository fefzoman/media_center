# Architecture

Phase 0 request paths:

```text
Desktop/LG browser -> nginx :80 -> /tv/ static HTML/CSS/JS
                               -> /api/ -> FastAPI :8000
                               -> /play/ -> 501 (reserved)
```

nginx is the only published service. FastAPI stays on the Compose network.
nginx waits for the backend health check before starting. Its configuration is
rendered by the official image so `MEDIA_CENTER_PORT` changes both the backend
listener and nginx upstream. The API URI is preserved by `proxy_pass` without
a URI suffix. Same-origin browser requests require no CORS configuration.

The backend uses Python 3.12+, FastAPI and Pydantic with a `src` layout.
Environment configuration is validated at process startup. The image runs as
a non-root user. The named `/data` volume is reserved for SQLite metadata;
no database is opened and no movie files are written in this phase.

Empty domain packages establish boundaries without implementing future phases:
catalog, playback, torrents, metadata and persistence. SQLAlchemy is deferred
until the catalog needs persistence. httpx is currently a TestClient dependency;
the future torrent adapter will use it with explicit network timeouts.

Phase 1 adds TorrServer-LT-gst and all engine HTTP calls behind `torrents/`.
Verify the actual upstream image/API before adding the service. Future playback
prefers direct HTTP, then HLS remux/audio conversion, then video transcode.
RAM-only cache configuration must be applied and verified against that engine;
the reserved environment variables alone do not enforce it.

The frontend uses ES5-style JavaScript and XMLHttpRequest, without frameworks,
modules or a build step. The initial page has one focusable action and a bounded
connection check. Full D-pad catalog navigation and video playback arrive in
Phase 3. webOS packaging waits until browser playback is proven on the actual TV.

Implementation references consulted for bootstrap:

- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/)
- [nginx proxy URI handling](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_pass)
- [Ruff configuration](https://docs.astral.sh/ruff/configuration/)
- [pytest configuration](https://docs.pytest.org/en/stable/reference/customize.html)
