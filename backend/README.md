# Parallax Politics Backend

Production-grade agentic backend for **Parallax Politics** — FastAPI + async SQLAlchemy + Postgres + Redis, powering a multi-agent system (DCAA, DEMCAA, SGA, PPA, Strategist, Commander) on OpenRouter Google Gemma with hard token-budget governance and EXA web search.

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
```

API docs: http://localhost:8000/docs

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
