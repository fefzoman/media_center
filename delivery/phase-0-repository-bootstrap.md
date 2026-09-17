# Phase 0 — Repository bootstrap

## Purpose

Phase 0 established a small, runnable foundation for the media center. Its
purpose was to prove that the Dell can host one LAN origin that an LG webOS
browser can open, while creating clear boundaries for the torrent, catalog,
playback, metadata, persistence, and webOS work that follows.

## What was delivered

### Repository and service structure

- Created the FastAPI backend under `backend/src/media_center/` using a `src`
  layout.
- Created separate packages for API, catalog, metadata, persistence, playback,
  and torrent responsibilities.
- Added the static TV frontend under `frontend/` and infrastructure under
  `infra/`.
- Added placeholders for later webOS packaging under `webos/`.

This structure keeps TV code, application logic, infrastructure, and future
storage concerns separate, so later phases can grow without putting every
responsibility in the API routes.

### Browser-first frontend

- Added a lightweight HTML, CSS, and conservative JavaScript page at `/tv/`.
- Added a visible focus state and a connection check suitable for initial LG
  browser testing.
- Avoided a frontend build system so the Dell can serve the files directly and
  older TV browsers have fewer compatibility risks.

The first UI intentionally tests reachability before catalog and remote-control
navigation are introduced.

### FastAPI foundation

- Added validated environment configuration with Pydantic.
- Added `GET /api/v1/health` as the initial service health contract.
- Exposed OpenAPI at `/api/openapi.json` and developer documentation at
  `/api/docs`.
- Added a non-root backend container based on Python 3.12.

The health endpoint provided a stable path for Compose startup checks, nginx
proxy verification, and the frontend connection indicator.

### nginx and Docker Compose

- Added nginx as the only public HTTP entry point.
- Routed `/tv/` to static frontend files and `/api/` to FastAPI.
- Kept the backend port on the private Compose network.
- Added Compose health checks and startup ordering.
- Reserved named storage for future application metadata.

Using one HTTP origin avoids CORS requirements and gives the TV a single LAN
address for the UI, API, and future playback streams.

### Developer workflow and documentation

- Added `Makefile` targets for bootstrap, development, linting, tests, Compose,
  logs, and smoke checks.
- Added Ruff, pytest, shell bootstrap scripts, and an environment template.
- Added architecture, API, operations, and webOS documentation.
- Added repository-specific instructions in `AGENTS.md`.

These files make a fresh checkout reproducible and provide one documented set
of commands for local development and deployment on the Dell.

## Validation performed

- Built and started the Compose stack.
- Confirmed nginx could serve `/tv/` and proxy the health endpoint.
- Confirmed redirects and static assets through the smoke-test script.
- Ran Ruff formatting and lint checks.
- Ran the Phase 0 pytest suite.

## Result and next-phase boundary

At the end of Phase 0, the browser could reach the Dell-hosted application and
the repository had a tested service skeleton. Torrent registration and video
streaming were deliberately left for Phase 1.
