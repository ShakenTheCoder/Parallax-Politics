#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"

api_pid=""
worker_pid=""
frontend_pid=""

cleanup() {
  trap - EXIT INT TERM

  for pid in "$api_pid" "$worker_pid" "$frontend_pid"; do
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      kill -TERM "$pid" 2>/dev/null || true
    fi
  done

  wait 2>/dev/null || true
}

trap cleanup EXIT
trap 'cleanup; exit 130' INT TERM

command -v docker >/dev/null 2>&1 || {
  echo "Error: Docker is required. Start Docker Desktop and try again." >&2
  exit 1
}
command -v uv >/dev/null 2>&1 || {
  echo "Error: uv is required. Run the one-time backend setup first." >&2
  exit 1
}
command -v npm >/dev/null 2>&1 || {
  echo "Error: npm is required. Run the one-time frontend setup first." >&2
  exit 1
}

if [[ ! -d "$ROOT_DIR/node_modules" ]]; then
  echo "Installing frontend dependencies..."
  (cd "$ROOT_DIR" && npm ci)
fi

if [[ ! -x "$BACKEND_DIR/.venv/bin/python" ]]; then
  echo "Installing backend dependencies..."
  (cd "$BACKEND_DIR" && uv sync --extra dev)
fi

echo "Starting infrastructure..."
(
  cd "$BACKEND_DIR"
  docker compose up -d --wait
  uv run alembic upgrade head
)

echo "Starting backend API..."
(
  cd "$BACKEND_DIR"
  exec uv run uvicorn app.main:app --reload --port 8000
) &
api_pid=$!

echo "Starting background worker..."
(
  cd "$BACKEND_DIR"
  exec uv run arq app.worker.WorkerSettings
) &
worker_pid=$!

echo "Starting frontend..."
(
  cd "$ROOT_DIR"
  exec npm run dev
) &
frontend_pid=$!

echo ""
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
echo "Press Ctrl-C to stop the API, worker, and frontend."

while true; do
  for pid in "$api_pid" "$worker_pid" "$frontend_pid"; do
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "A development process exited; stopping the remaining processes." >&2
      exit 1
    fi
  done
  sleep 1
done
