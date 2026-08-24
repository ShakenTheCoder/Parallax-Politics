.PHONY: help up down dev worker migrate test lint typecheck fmt

help:
	@echo "Targets:"
	@echo "  up        - start postgres + redis (docker compose)"
	@echo "  down      - stop infra"
	@echo "  dev       - run the FastAPI dev server (autoreload)"
	@echo "  worker    - run scheduled intelligence collection"
	@echo "  migrate   - apply alembic migrations to head"
	@echo "  test      - run pytest"
	@echo "  lint      - ruff check"
	@echo "  fmt       - ruff format"
	@echo "  typecheck - mypy strict"

up:
	docker compose up -d

down:
	docker compose down

dev:
	uv run uvicorn app.main:app --reload --port 8000

worker:
	uv run arq app.worker.WorkerSettings

migrate:
	uv run alembic upgrade head

test:
	uv run pytest -q

lint:
	uv run ruff check app tests

fmt:
	uv run ruff format app tests

typecheck:
	uv run mypy app
