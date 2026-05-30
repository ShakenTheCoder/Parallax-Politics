"""Pytest fixtures.

Tests use:
- the real Postgres + Redis already running via docker compose (so we exercise
  JSONB / asyncpg / Redis pub-sub paths exactly as in prod).
- LLM_DISABLED=true (kill switch) so no OpenRouter / EXA calls are made.

If you need a fully hermetic CI run, swap to aiosqlite + fakeredis — the
agent code paths are identical.
"""
from __future__ import annotations

import os
import sys
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

# Ensure kill switch is on for the entire test session.
os.environ.setdefault("LLM_DISABLED", "true")
os.environ.setdefault("EXA_API_KEY", "")  # force EXA mocks too

# Make backend root importable when running `pytest` from anywhere.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture
async def db_session() -> AsyncIterator:
    from app.db import session_scope
    async with session_scope() as s:
        yield s
