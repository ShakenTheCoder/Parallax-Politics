# Superadmin console

Superadmin credentials open `/admin`. The navigation exposes:

- **Identities** — `/admin`
- **Political Glossary** — `/admin/glossary`
- **Intelligence** — `/intelligence`

All administrative backend endpoints require a valid superadmin bearer token.

## Frontend routes

| Path | Contents |
| --- | --- |
| `/admin` | Principal identity registry, new-identity creation, PIDAA status, identity detail links, rerun/archive actions, and existing user removal. |
| `/identity?profileId=<id>` | Full dossier for one principal identity. Opened from the identity registry. |
| `/admin/glossary` | The political-figure glossary, intended to cover the monitored 30-person set. |
| `/admin/glossary/<slug>` | One glossary figure’s dossier, social accounts, coverage gaps, source ledger, and live refresh action. |
| `/intelligence` | Glossary-wide public activity monitor: people, evidence feed, analytics, and source registry. “Run monitor now” triggers a bounded collection batch. |
| `/superadmin/enter` | Legacy entry path; redirects to `/login`. |
| `/analysis` | Reserved route shell; not the operational monitoring view. |
| `/audience` | Legacy route that redirects to `/analysis`; admins are redirected to `/admin` by the legacy component. |

## Backend endpoint inventory

All paths below are relative to `http://localhost:8000` and are prefixed with `/api/v1`.

### Identity and glossary management

- `POST /admin/disambiguate` — find a candidate identity without creating records.
- `POST /admin/principals` — create the profile, principal login, identity skeleton, and PIDAA run; returns one-time credentials.
- `GET /admin/principals` — list principal identities.
- `GET /admin/principals/{profile_id}` — retrieve a full principal dossier.
- `POST /admin/principals/{profile_id}/rerun` — rerun PIDAA.
- `DELETE /admin/principals/{profile_id}` — archive a principal.
- `GET /admin/glossary/figures` — list glossary figures.
- `GET /admin/glossary/figures/{slug}` — retrieve one glossary figure.
- `POST /admin/glossary/seed` — queue glossary seeding; verify the current implementation before using it.
- `POST /admin/glossary/figures/{slug}/refresh` — queue a live glossary refresh.

### User administration and observability

- `GET /admin/users` — list login accounts.
- `POST /admin/users` — legacy generic account creation endpoint; not exposed by the current UI.
- `DELETE /admin/users/{user_id}` — remove an account.
- `GET /admin/usage` — LLM usage, cost, and Redis budget rollups.

### Worker activity monitor

- `GET /intelligence/activity-monitor?window=6h|24h|7d` — monitoring picture for the glossary people.
- `GET /intelligence/activity-monitor/sources` — approved activity source registry.
- `POST /intelligence/activity-monitor/sources/bootstrap` — idempotently bootstrap the source registry.
- `POST /intelligence/activity-monitor/collect` — run one bounded collection and Ollama analysis batch.
- `GET /intelligence/agents` — registered agent fleet and operating invariant.

The activity worker is started with `uv run arq app.worker.WorkerSettings`. It leases scheduled work from Redis and persists normalized results in PostgreSQL.
