#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if [ ! -x .venv/bin/python ]; then
    printf '%s\n' 'Run make bootstrap first.' >&2
    exit 1
fi
# Local development reads the process environment; .env is managed by Compose.
exec .venv/bin/python -m media_center
