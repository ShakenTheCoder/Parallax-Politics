# Parallax Politics — handoff index

Parallax Politics is a restricted Philippine political-intelligence platform. It combines identity dossiers, a political-figure glossary, public activity monitoring, background agents, and principal-facing briefs.

Read these notes in order:

1. [Run the app](./01-run-the-app.md)
2. [Tech stack and integrations](./02-tech-stack-and-integrations.md)
3. [Authentication and account lifecycle](./03-auth-and-account-lifecycle.md)
4. [Superadmin console](./04-superadmin-console.md)
5. [Principal user experience](./05-principal-user.md)

Important current-state notes:

- The preferred launcher is [`start.sh`](../start.sh).
- The old seed command is documented in older files but unavailable: `backend/app/scripts/seed.py` does not exist.
- The user-facing analysis shell at `/analysis` is currently reserved; the operational worker monitor is `/intelligence` and is superadmin-only.
- Existing working-tree changes may represent active product work. Inspect `git status` before changing unrelated files.
