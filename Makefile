PYTHON ?= python3
BASE_URL ?= http://localhost
VENV_BIN := .venv/bin

.PHONY: bootstrap up down logs dev test lint format check smoke config

bootstrap:
	PYTHON="$(PYTHON)" ./scripts/bootstrap.sh

up:
	docker compose up --build -d --wait

down:
	docker compose down

logs:
	docker compose logs -f

dev:
	./scripts/dev.sh

test:
	$(VENV_BIN)/python -m pytest

lint:
	$(VENV_BIN)/ruff check .
	$(VENV_BIN)/ruff format --check .

format:
	$(VENV_BIN)/ruff format .

check: lint test

smoke:
	PYTHON="$(PYTHON)" ./scripts/smoke-test.sh "$(BASE_URL)"

config:
	docker compose config --quiet
