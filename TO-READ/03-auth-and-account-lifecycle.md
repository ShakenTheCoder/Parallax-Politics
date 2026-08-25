# Authentication and account lifecycle

There is no public registration flow. The login page is `/login`; users receive credentials from the superadmin.

## Login flow

1. A user submits username and password at `/login`.
2. Next.js sends the request through `/api/session/login` to the backend `POST /api/v1/auth/login`.
3. FastAPI verifies the bcrypt password hash and applies Redis-backed login attempt limits.
4. The backend returns a bearer token and user metadata.
5. Next.js stores the token in a server-managed HttpOnly session cookie.
6. Superadmins go to `/admin`; principal users go to `/brief`.

The browser does not receive the backend bearer token. Authenticated frontend API calls use the same-origin `/api/backend/[...path]` proxy.

## Account creation

The canonical product flow is superadmin → **Add New Identity**:

1. Superadmin searches a person through `POST /api/v1/admin/disambiguate`.
2. Superadmin confirms the candidate through `POST /api/v1/admin/principals`.
3. The backend creates the profile, principal user, identity skeleton, and PIDAA run.
4. Generated credentials are returned once in the confirmation modal. The password is stored only as a hash and cannot be retrieved later.
5. The background work builds the identity dossier; the principal then logs in with those credentials.

The generic backend `POST /api/v1/admin/users` endpoint still exists for compatibility, but its form is no longer exposed in the UI. Treat the identity flow as the supported account-creation path.

## Roles

- `superadmin`: administrative console, glossary management, identity management, and worker activity monitoring.
- `principal`: own brief and associated activity/competitor information.

There is no self-service registration. To remove an account, a superadmin uses the user table on `/admin`; the last superadmin and the currently logged-in superadmin cannot be deleted.
