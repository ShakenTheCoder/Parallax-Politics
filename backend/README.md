# Parallax Politics Backend

Political-intelligence control plane for **Parallax Politics** — FastAPI, async SQLAlchemy, Postgres, Redis, provenance-bearing public evidence, bounded scenario estimates, and analyst-approved strategic verdicts.

## Stack

- **API**: FastAPI (async), Uvicorn / Gunicorn
- **DB**: PostgreSQL 16 via SQLAlchemy 2.0 async + Alembic
- **Cache / event bus / budget counters**: Redis 7
- **Background jobs**: arq
- **LLM**: OpenRouter (Google Gemma 4 31B) with free tier
- **Search**: EXA
- **Tooling**: `uv` for envs + deps, `ruff` + `mypy` + `pytest`

## Quickstart

```bash
# 1. Copy env
cp .env.example .env
# edit OPENROUTER_API_KEY and EXA_API_KEY

# 2. Start infra
docker compose up -d

# 3. Install deps
uv sync --extra dev

# 4. Run migrations
uv run alembic upgrade head

# 5. Seed DB (creates Sara Duterte profile + login)
uv run python -m app.scripts.seed

# 6. Start API
uv run uvicorn app.main:app --reload --port 8000

# 7. In a second process, start durable scheduled collection
uv run arq app.worker.WorkerSettings
```

API docs: http://localhost:8000/docs

## Intelligence operations

- Apply every migration before starting the API: `uv run alembic upgrade head`.
- Administrators register an explicit source authority and URL/path allowlist in `/intelligence`.
- The public-web connector permits only public HTTP(S), public DNS addresses, ports 80/443, same-origin redirects, allowlisted paths, HTML under 2 MB, and robots-permitted requests. It does not support authentication, stealth, CAPTCHA bypass, or proxy rotation.
- A monitoring assignment binds one registered source/path to one Observed Candidate. The ARQ worker leases due assignments every minute and applies bounded retry backoff.
- Polling, consented panels, platform APIs, and licensed feeds are represented as connector boundaries. They require contracts and credentials before ingestion; they never fall back to public scraping.
- Scenario outputs are explicitly estimates. They use only time-bounded evidence, suppress cohorts below 100 observations, cap uncalibrated confidence, expire after 24 hours, and remain drafts until an administrator records an analyst decision.
- TRIBE v2 is intentionally excluded from electorate-response estimates: it predicts fMRI responses, is not validated for political opinion inference, and its public release is non-commercial. See `../docs/adr/0002-do-not-use-tribe-v2-for-electoral-response.md`.

The optional local high-volume data-plane scaffold is in `docker-compose.intelligence.yml`. It binds Redpanda, MinIO, ClickHouse, and OpenSearch to localhost for development only; production deployments require private networking, managed credentials, encryption, backups, and service-specific authorization.

## Budget governance

Hard limits enforced via Redis atomic counters:

- **$25/day** global LLM spend (for budget tracking)
- **$0.50/run** orchestrator budget
- **$5/day** escalation sub-cap (for budget tracking)
- **$0.00** actual cost with Google Gemma free tier
- `LLM_DISABLED=true` short-circuits all LLM calls to deterministic mocks

See `app/llm/budget.py`.

## Layout

```
app/
  main.py            FastAPI entry
  config.py          pydantic-settings
  db.py              async engine + session
  redis.py           client + pub/sub helpers
  api/v1/            REST + SSE endpoints
  agents/            DCAA, DEMCAA, SGA, PPA, Strategist, Commander
  llm/               OpenRouter client, router, budget, prompts/
  search/            EXA wrapper
  models/            SQLAlchemy models
  schemas/           Pydantic DTOs
  services/          orchestrator, evidence store
  eventbus/          Redis pub/sub
  telemetry/         structlog, tracing
  scripts/           seed, admin tooling
```
