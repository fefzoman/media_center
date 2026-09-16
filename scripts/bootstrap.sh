#!/bin/sh
set -eu
cd "$(dirname "$0")/.."

python_bin=${PYTHON:-python3}
"$python_bin" -c 'import sys; sys.exit("Python 3.12+ is required; set PYTHON to a suitable interpreter.") if sys.version_info < (3, 12) else None'
if [ ! -d .venv ]; then
    "$python_bin" -m venv .venv
fi
.venv/bin/python -m pip install -e './backend[dev]'
if [ ! -e .env ]; then
    cp .env.example .env
fi
printf '%s\n' 'Ready. Run make check, then make up.'
