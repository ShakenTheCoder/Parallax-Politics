# Tech stack and integrations

## Application

- Next.js `16.2.6` App Router, React `19.2.4`, TypeScript.
- Tailwind CSS `4` and Motion for the frontend UI.
- FastAPI with Uvicorn for the backend API.
- Async SQLAlchemy `2.x`, PostgreSQL `16`, and Alembic migrations.
- Redis `7` for caching, rate limits, pub/sub, event state, and budget counters.
- ARQ for the durable background worker and scheduled collection jobs.
- `uv` for Python environments and locked dependencies.
- Ruff, mypy, and pytest for backend quality checks; ESLint for frontend linting.

## Intelligence integrations

- **Scrapling**: approved public-web acquisition, including the bounded browser-based fetch path. Source URLs and paths are allowlisted; authentication, stealth bypasses, proxy rotation, and arbitrary page actions are not exposed as product features.
- **Ollama**: optional local OpenAI-compatible LLM provider. Configure `LLM_PROVIDER=ollama`, `OLLAMA_BASE_URL`, and the model names in `backend/.env`.
- **NVIDIA NIM**: hosted OpenAI-compatible LLM provider. The default configuration uses NVIDIA unless `LLM_PROVIDER` is changed.
- **EXA**: evidence search and source discovery for identity and intelligence agents. `EXA_API_KEY` is required for those flows.
- **PostgreSQL + Redis**: persistence, queues, event communication, rate limiting, and token/cost budget tracking.

## Main domain agents

The backend contains PIDAA identity analysis plus the brief/orchestration agents, including SGA, DCAA, DEMCAA, PPA, Strategist, and Commander boundaries. Generated material is expected to remain evidence-backed; provider failures should be visible rather than replaced with fabricated defaults.

## Configuration

Copy `backend/.env.example` to `backend/.env`. Keep credentials out of git. The frontend uses a server-only backend proxy; bearer tokens are stored in an HttpOnly cookie and are not exposed to the browser as a public environment variable.
