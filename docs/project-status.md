# Project Status

**Snapshot date:** 2026-08-11  
**Branch:** `audience-center`  
**Base commit:** `758bbba` (`feat: initial platform implementation`)  
**Latest repair checkpoint:** current `HEAD` (`fix: require real provider-backed intelligence`)
**Repository:** local Git repository with an existing `origin` remote; no push performed.

## Current stage

Parallax Politics is at an integrated frontend/backend implementation checkpoint. The product is a restricted-access political intelligence platform for a Philippine political context. The current work adds the first end-to-end shape of the Audience Center and intelligence control plane on top of the earlier brief, authentication, principal identity, and administrative flows.

### Frontend

- Next.js 16.2.6 App Router application with server-only backend proxying and HttpOnly session cookies.
- User-facing routes include `/`, `/login`, `/brief`, `/identity`, `/audience`, `/analysis`, and `/auth`.
- Administrative routes include `/admin` and `/superadmin/enter`.
- New or expanded views cover principal identity review, audience instructions, intelligence overview, sources, subscriptions, scenarios, and verdict review.
- Existing design direction remains documented in `UI-AESTHETIC.md` and `UI-ELEMENTS.md`.

### Backend

- FastAPI control plane with async SQLAlchemy, PostgreSQL, Redis, Alembic, ARQ, NVIDIA NIM, and EXA integration boundaries.
- Existing identity, brief, auth, profile, search, run, and admin APIs remain in place.
- New API surfaces include:
  - `/api/v1/audience` for on-demand audience analysis and instruction retrieval.
  - `/api/v1/intelligence` for agent fleet status, collection sources, subscriptions, scenarios, and analyst verdicts.
- New domain components include audience agents, intelligence collection/policy/population services, competitor and intelligence models, schemas, migrations, a scheduled worker, and source-backed portrait resolution.
- The platform preserves the documented vocabulary and guardrails in `CONTEXT.md` and the ADRs under `docs/adr/`.

## Repository state

This directory was already a Git repository before this handoff:

```text
758bbba (HEAD -> audience-center, origin/main, origin/HEAD, main)
feat: initial platform implementation
3667cf8 Initial commit from Create Next App
```

The repository is connected to `https://github.com/ShakenTheCoder/Parallax-Politics.git` as `origin`. The current implementation changes were uncommitted at the start of this work. A local repair checkpoint is created after validation. GitHub remains unchanged until an explicit push is requested.

## Validation snapshot

| Check | Result | Notes |
|---|---|---|
| `npm run build` | Pass after repair | Next.js production build and TypeScript validation complete successfully. |
| `npm run lint` | Pass with warnings | React hook/state errors are resolved; remaining warnings are mostly image optimization and unused legacy UI code. |
| `cd backend && uv run pytest -q tests/unit` | Pass | 28 unit tests pass against running PostgreSQL/Redis services. |
| `cd backend && uv run pytest -q` | Not completed | The legacy full orchestrator integration test invokes live EXA/NVIDIA calls and did not finish during the bounded validation run. |
| `cd backend && uv run ruff check app tests` | Pass | All backend Ruff checks pass. |
| `cd backend && uv run alembic upgrade head` | Pass | Current database revision is `o0b6c7d8e9f3`. |
| `curl http://127.0.0.1:8000/health` | Pass | FastAPI started successfully and returned version `0.1.0`. |

## Recommended next checkpoint

1. Replace or narrow the legacy full orchestrator integration test so live provider calls have explicit timeouts and do not block the test runner.
2. Remove the remaining unused `IdentityDrawer` UI code and image warnings if a zero-warning frontend lint gate is required.
3. Exercise an authenticated end-to-end brief/audience flow with a real principal and provider-backed responses.

## Working commands

```bash
# frontend
npm install
npm run dev
npm run build
npm run lint

# backend
cd backend
uv sync --extra dev
cp .env.example .env
make up
make migrate
make test
make lint
make typecheck
```

Runtime analytical calls now require provider responses. There is no LLM/EXA mock mode or deterministic synthetic result path. Do not commit `.env` files or credentials; only the checked-in `.env.example` files are intended for configuration guidance.

## Principal command-center completion

- Analysis, evidence, and appearance projections are database-backed and principal-scoped.
- Poll releases have strict provenance fields, admin verification, and a seeded reviewed Pulse Asia record.
- Audience Lab runs three provider-backed samples across all configured cohorts and variants; failures are persisted as unavailable.
- Principal briefs persist `agent_draft`, `approved`, or `rejected` review state. Only superadmins can review.
- Migration head for these capabilities: `t3e4f5a6b7c8`.
