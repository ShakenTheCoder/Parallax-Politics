# Run the app

From the repository root:

```bash
cd /Users/ioan_andrei/Desktop/Parallax-TEST-V1/political-platform
```

## One-time setup

```bash
npm ci
cd backend
uv sync --extra dev
```

Make sure Docker Desktop is running.

## Recommended: one launcher

From the repository root:

```bash
./start.sh
```

`start.sh` installs missing dependencies, starts PostgreSQL and Redis, waits for them, applies Alembic migrations, and starts the API, ARQ worker, and Next.js frontend. Press `Ctrl-C` to stop the API, worker, and frontend. Docker infrastructure remains running.

## Manual four-terminal startup

Terminal 1 — infrastructure:

```bash
cd /Users/ioan_andrei/Desktop/Parallax-TEST-V1/political-platform/backend
docker compose up -d
uv run alembic upgrade head
```

Terminal 2 — backend API:

```bash
cd /Users/ioan_andrei/Desktop/Parallax-TEST-V1/political-platform/backend
uv run uvicorn app.main:app --reload --port 8000
```

Terminal 3 — background worker:

```bash
cd /Users/ioan_andrei/Desktop/Parallax-TEST-V1/political-platform/backend
uv run arq app.worker.WorkerSettings
```

Terminal 4 — frontend:

```bash
cd /Users/ioan_andrei/Desktop/Parallax-TEST-V1/political-platform
npm run dev
```

URLs:

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Health: http://localhost:8000/health
- OpenAPI docs: http://localhost:8000/docs

Stop infrastructure separately:

```bash
cd /Users/ioan_andrei/Desktop/Parallax-TEST-V1/political-platform/backend
docker compose down
```

The documented seed command is unavailable because `backend/app/scripts/seed.py` does not exist. Account and identity creation currently happens through the superadmin identity flow.
