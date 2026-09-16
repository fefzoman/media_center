# My Media

A self-hosted media center for an LG webOS TV, hosted on a Dell running
Debian 13. **Phase 0: repository bootstrap** is implemented. The current UI
checks server connectivity; movie catalog and torrent playback come later.

## Run the stack

Install Docker Engine/Desktop with Docker Compose v2+ and start the daemon.
From this directory:

```sh
cp .env.example .env
# Set TV_BASE_URL to the Dell's LAN address in .env.
docker compose up --build
```

No `.env` file is required to start with defaults. On a fresh checkout,
`docker compose up` builds the backend automatically. After code changes use
`--build`. Only nginx publishes a host port (80 by default).

- TV/browser: `http://localhost/tv/` or `http://DELL_LAN_IP/tv/`
- Health: `http://localhost/api/v1/health`
- Developer API docs: `http://localhost/api/docs`

```json
{"status":"ok","torrserver":"not_configured"}
```

Health is backend liveness, not a claim that playback is ready. TorrServer's
container, dependency probe and adapter are Phase 1 work. `/play/` currently
returns 501. There are no fake catalog/playback endpoints.

If port 80 is occupied, set `HTTP_PORT=8080` in `.env` and use
`http://localhost:8080`. For LAN use, keep this deployment behind your home
router without port forwarding; `HTTP_BIND_ADDRESS` can restrict nginx to the
Dell's LAN IP. `127.0.0.1` is suitable for desktop-only development.

## Develop and verify

Use Python 3.12+ with `venv`, pip and make. For Debian, install the matching
Python venv package if needed. A host Python installation is only needed for
local development/checks; the deployed backend uses Python 3.12 in Docker.

```sh
make bootstrap                  # creates .venv and .env if absent
# Or: make bootstrap PYTHON=python3.13
make check                      # Ruff, formatting check, pytest
make up                         # builds, starts, waits for backend health
make smoke                      # checks nginx -> backend and TV static assets
# Alternate port: make smoke BASE_URL=http://localhost:8080
make logs
make down                       # stops containers; preserves the data volume
```

With `.venv` active, `ruff check .`, `ruff format --check .` and `pytest`
also work from the repository root. `make format` applies formatting.
`make dev` runs only the backend at port 8000; local settings come from exported
environment variables, while Docker Compose reads `.env`. For example:

```sh
MEDIA_CENTER_HOST=127.0.0.1 MEDIA_CENTER_PORT=9000 make dev
```

Use the Compose stack to develop the frontend at the same origin as the API.
Static assets are mounted read-only and edits appear on browser refresh.

## Repository map

| Path | Responsibility |
| --- | --- |
| `backend/src/media_center/` | FastAPI, configuration, future domain modules |
| `backend/tests/` | pytest endpoint/configuration tests |
| `frontend/` | Plain HTML/CSS/JavaScript; no build pipeline |
| `infra/nginx/` | Static hosting and versioned API reverse proxy |
| `infra/torrserver/` | Phase 1 integration notes |
| `webos/` | Phase 6 packaging placeholder |
| `scripts/` | Bootstrap, local backend, stack smoke checks |
| `docs/` | Architecture, API, operation and TV notes |

Read [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for the complete roadmap,
[architecture](docs/architecture.md), [API](docs/api.md),
[operations](docs/operations.md), and [webOS notes](docs/webos.md).
Only use media you are authorized to access/distribute via BitTorrent.
