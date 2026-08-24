# Parallax Politics

Political observation and advisory center for provenance-bearing public evidence, aggregate population analysis, competitive intelligence, scenario estimates, and analyst-approved strategy.

## Getting Started

First, run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

The browser never receives the backend bearer token. Next.js stores it in a strict HttpOnly cookie and forwards authenticated requests through same-origin `/api/backend/*` route handlers. Set the server-only `BACKEND_API_BASE` value from `.env.example`; do not expose it as a `NEXT_PUBLIC_` variable.

Backend setup, migrations, the scheduled collection worker, source-policy constraints, and the optional data-plane services are documented in [backend/README.md](backend/README.md).

The current implementation checkpoint, validation results, and recommended next work are recorded in [docs/project-status.md](docs/project-status.md).

## Project Structure

- `src/app/` - Next.js app router pages
- `src/lib/` - API client and session management
- `src/components/` - React components (Navbar, etc.)
- `backend/` - FastAPI backend with multi-agent system

## Learn More

This project uses [Next.js](https://nextjs.org) with the App Router.
