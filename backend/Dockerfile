# syntax=docker/dockerfile:1.7
# Multi-stage Parallax backend image.
# Targets: `api` (default) and `worker` (future arq).

FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    UV_SYSTEM_PYTHON=1 \
    UV_LINK_MODE=copy

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /usr/local/bin/uv

WORKDIR /app

# Dependency layer (cached separately from source).
COPY pyproject.toml uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system .
RUN patchright install --with-deps chromium \
    && chmod -R a+rX /ms-playwright

# Source.
COPY . .

# Drop privileges.
RUN useradd -m -u 10001 -s /usr/sbin/nologin parallax \
    && chown -R parallax:parallax /app
USER parallax

EXPOSE 8000

# --- API target (default) ---------------------------------------------------
FROM base AS api
CMD ["gunicorn", "app.main:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "-w", "2", "-b", "0.0.0.0:8000", \
     "--access-logfile", "-", "--error-logfile", "-", \
     "--timeout", "120", "--graceful-timeout", "30"]

# --- Worker target ---------------------------------------------------------
# MVP runs orchestrator via FastAPI BackgroundTasks. When traffic justifies,
# swap in arq:  CMD ["arq", "app.workers.WorkerSettings"]
FROM base AS worker
CMD ["python", "-c", "print('worker target ready; wire arq.WorkerSettings to enable.')"]
