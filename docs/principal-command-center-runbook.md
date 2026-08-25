# Principal Command Center Runbook

## Data flow

Collectors persist `SignalEvent` and `PoliticalActivity` records with source
and capture metadata. `/api/v1/intelligence/analysis` projects those rows for
the authenticated principal. Principals are always scoped to `user.principal_id`;
superadmins must provide a valid `profile_id`.

`/brief` combines the live projection with the latest persisted generated brief.
Generated briefs run SGA → DCAA/DEMCAA → Strategist/Brief and start as
`agent_draft`. Review is performed through `PATCH /api/v1/briefs/{brief_id}/review`.

## Polls

Import a poll through `POST /api/v1/intelligence/polls` as a superadmin. Verify
it with `PATCH /api/v1/intelligence/polls/{poll_id}/review`. The migration seeds
the reviewed Pulse Asia July 2026 release as a provenance-bearing observed
record; it remains a polling-layer record.

## Audience Lab

Submit one to three message variants to
`POST /api/v1/intelligence/audience-experiments`. The API queues a run and the
worker executes three provider-backed samples. Poll
`GET /api/v1/intelligence/audience-experiments/{run_id}` until `completed` or
`failed`. Provider failure is visible as `provider_status=unavailable`; no
fallback score is generated.

## Operational checks

Run `alembic upgrade head`, start PostgreSQL/Redis/API/worker/frontend, then
exercise principal isolation and the superadmin review flow. Missing feeds,
stale snapshots, and provider failures should remain visible in the UI.
