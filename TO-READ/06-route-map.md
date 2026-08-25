# Route map

## Frontend routes

| Path | Access / purpose |
| --- | --- |
| `/` | Public landing page. |
| `/login` | Credential login. |
| `/auth` | Auth-related legacy/page surface; inspect before extending. |
| `/brief` | Principal brief and activity workspace. |
| `/identity?profileId=<id>` | Identity dossier detail, primarily opened by superadmins. |
| `/admin` | Superadmin identity and user management. |
| `/admin/glossary` | Superadmin 30-person political glossary. |
| `/admin/glossary/<slug>` | Glossary figure detail. |
| `/intelligence` | Superadmin worker activity monitor. |
| `/analysis` | Principal live Analysis Center; superadmins select `profile_id` through the API. |
| `/audience` | Legacy redirect to `/analysis`. |
| `/superadmin/enter` | Legacy redirect to `/login`. |

## Server-side frontend routes

- `/api/session/login` — forwards login to FastAPI and sets the HttpOnly session cookie.
- `/api/session/logout` — clears the session cookie.
- `/api/backend/[...path]` — same-origin authenticated proxy to `/api/v1/*`.

## Backend infrastructure URLs

- `http://localhost:8000/health` — health check.
- `http://localhost:8000/docs` — interactive FastAPI OpenAPI documentation.
- `http://localhost:8000/openapi.json` — OpenAPI schema.

## Live evidence APIs

- `GET/POST /api/v1/intelligence/polls` — list or superadmin-import representative polls.
- `PATCH /api/v1/intelligence/polls/{id}/review` — superadmin verification decision.
- `POST /api/v1/intelligence/audience-experiments` — queue up to three variants.
- `GET /api/v1/intelligence/audience-experiments/{run_id}` — provider run status and persisted samples.
- `PATCH /api/v1/briefs/{brief_id}/review` — superadmin brief review decision.
