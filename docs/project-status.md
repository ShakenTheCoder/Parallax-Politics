# Project Status

**Snapshot date:** 2026-08-11  
**Branch:** `audience-center`  
**Base commit:** `758bbba` (`feat: initial platform implementation`)  
**Repository:** local Git repository with an existing `origin` remote; no push performed.

## Current stage

Parallax Politics is at an integrated frontend/backend implementation checkpoint. The product is a restricted-access political intelligence platform for a Philippine political context. The current work adds the first end-to-end shape of the Audience Center and intelligence control plane on top of the earlier brief, authentication, principal identity, and administrative flows.

### Frontend

- Next.js 16.2.6 App Router application with server-only backend proxying and HttpOnly session cookies.
- User-facing routes include `/`, `/login`, `/brief`, `/identity`, `/audience`, `/intelligence`, and `/auth`.
- Administrative routes include `/admin` and `/superadmin/enter`.
- New or expanded views cover principal identity review, audience instructions, intelligence overview, sources, subscriptions, scenarios, and verdict review.
- Existing design direction remains documented in `UI-AESTHETIC.md` and `UI-ELEMENTS.md`.

### Backend

- FastAPI control plane with async SQLAlchemy, PostgreSQL, Redis, Alembic, ARQ, OpenRouter, and EXA integration boundaries.
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

The repository is connected to `https://github.com/ShakenTheCoder/Parallax-Politics.git` as `origin`. The current implementation changes were uncommitted at the start of this work. A local checkpoint commit is created after this document is added. GitHub remains unchanged until an explicit push is requested.

## Validation snapshot

| Check | Result | Notes |
|---|---|---|
| `npm run build` | Pass | Next.js production build and TypeScript validation complete successfully. |
| `npm run lint` | Fails | Existing checkpoint has React hook/state lint errors in `src/app/admin/page.tsx`, `src/app/audience/page.tsx`, `src/app/brief/page.tsx`, and other warnings. |
| `cd backend && uv run pytest -q` | Fails during collection | `tests/unit/test_router.py` imports `HAIKU_4_5`, which is not currently exported by `app.llm.router`. |
| `cd backend && uv run ruff check app tests` | Fails | 48 Ruff findings, including import ordering, unused imports, and style violations across existing and newly added code. |
| `cd backend && uv run alembic heads` | Not completed | The local `uv` environment could not spawn the `alembic` executable; verify the backend environment before running migrations. |

## Recommended next checkpoint

1. Repair the backend test/router contract (`HAIKU_4_5`) and rerun the full backend suite.
2. Resolve the frontend lint errors, starting with effect-triggered loading patterns and the module-level mutation in `brief/page.tsx`.
3. Run Ruff formatting/import fixes, then review behavior-sensitive findings manually.
4. Verify Alembic migrations against a local PostgreSQL instance and exercise the API/frontend flow with the backend services running.
5. Split the current broad checkpoint into focused commits before feature work continues, if a granular history is preferred.

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

Do not commit `.env` files or credentials. Only the checked-in `.env.example` files are intended for configuration guidance.
