# Principal user experience

Principal accounts are created by a superadmin during the identity-creation flow. A principal cannot register independently and does not see the administrative navigation.

## Main route

### `/brief`

This is the principal’s main workspace. It presents the latest evidence-backed political brief, including:

- current identity and dossier readiness;
- competitor landscape and competitor activity status;
- recent verified appearances and activity windows;
- topics grouped by lead, engage, or avoid stance;
- top risk, top opportunity, and next-move guidance;
- supporting sources and brief history.

If PIDAA or the evidence providers are unavailable, the UI should show an unavailable/loading state rather than substitute scores or fabricated content.

## Principal API surface

Paths are relative to `http://localhost:8000/api/v1`:

- `GET /auth/me` — current account metadata.
- `GET /briefs/me/identity` — the principal’s identity readiness and dossier summary.
- `POST /briefs` — queue a new brief build.
- `GET /briefs/active` — active brief state.
- `GET /briefs/latest` — latest completed brief.
- `GET /briefs` — brief history.
- `GET /briefs/{brief_id}` — one brief.
- `POST /briefs/{brief_id}/archive` — archive a brief.
- `GET /intelligence/brief?window=6h|24h|7d` — activity-aware brief view.
- `GET /intelligence/overview` — current intelligence overview for the authenticated user.

The principal-facing navigation intentionally contains only **Brief**. Administrative and worker-monitoring views are not part of the principal experience.
