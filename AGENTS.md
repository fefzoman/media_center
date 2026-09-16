# Repository Instructions

## Scope and precedence

Implement phases in `IMPLEMENTATION_PLAN.md` sequentially. Phase 0 is repository
bootstrap only; torrent integration starts in Phase 1 and webOS packaging in
Phase 6, after browser playback works.

## Project

This repository implements a self-hosted media center for LG webOS. The Dell
server handles torrent-backed progressive playback using TorrServer-LT-gst;
the TV is a thin HTTP/HLS client. The initial deployment is LAN-only.

## Architecture rules

- Isolate TorrServer calls behind the torrent backend adapter.
- Prefer Direct Play, then remux/audio conversion, then full video transcoding.
- Never require complete movie downloads or persistent movie storage.
- Keep LG-specific code out of the backend and torrent details out of the UI.
- Keep API routes under `/api/v1`; separate persistence models from handlers.
- Use typed Python 3.12+, FastAPI and Pydantic; add SQLAlchemy/SQLite in Phase 2.
- Set explicit timeouts on all outbound HTTP calls; never log secrets/source URLs.
- Use conservative HTML/CSS/JavaScript with visible focus and D-pad navigation.
- Do not introduce frontend frameworks/build pipelines without a concrete need.
- Never commit secrets or expose TorrServer to the public Internet.

## Development and checks

See `README.md` and `Makefile` for commands. Run `make check` before completing
backend changes (Ruff lint, formatting check, pytest). With the virtual environment
active, `ruff check .` and `pytest` also work from the repository root.
Add tests for non-trivial business logic; use `make smoke` against a running stack
for nginx/API integration. Do not claim LG compatibility without testing the TV.

## Mandatory MCP workflow

- At the start of every repository task, activate the current project with
  Serena and read its project instructions. Use Serena before opening source
  files when locating implementations, symbols, references, call paths, or
  related tests. Prefer its symbol-aware edit operations for structural changes.
- Before changing code or infrastructure that uses an external library, API,
  service, CLI, or Terraform provider, use Context7 first: resolve the library
  ID, query the current documentation for the exact behavior, and implement from
  that result. Do not guess a current interface from memory.
- Use `rg` first only for exact strings, configuration keys, error text, and
  regex searches. `code_index` may supplement Serena after the Serena pass.
- Do not silently bypass a required MCP call. If Serena or Context7 is unavailable,
  stop the affected work and report which server or tool failed.
- Every implementation report must state what Serena inspected and which
  Context7 documentation was consulted. For a task with no external dependency,
  explicitly state that the Context7 gate was not applicable.
