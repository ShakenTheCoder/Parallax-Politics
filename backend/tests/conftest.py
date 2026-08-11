"""Pytest fixtures.

Tests use the real Postgres + Redis services started by docker compose so we
exercise JSONB, asyncpg, and Redis paths exactly as in production.
"""

from __future__ import annotations

import sys
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

# Make backend root importable when running `pytest` from anywhere.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture
async def db_session() -> AsyncIterator:
    from app.db import session_scope

    async with session_scope() as s:
        yield s
