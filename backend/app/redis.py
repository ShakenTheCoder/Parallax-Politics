"""Async Redis client + pub/sub helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import orjson
from redis.asyncio import Redis, from_url

from app.config import get_settings

_client: Redis | None = None


def get_redis() -> Redis:
    """Return the process-wide async Redis client."""
    global _client
    if _client is None:
        _client = from_url(
            get_settings().redis_url,
            encoding="utf-8",
            decode_responses=True,
            health_check_interval=30,
        )
    return _client


async def close_redis() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


# --- Pub/Sub event bus -------------------------------------------------------


async def publish(channel: str, payload: dict[str, Any]) -> int:
    return await get_redis().publish(channel, orjson.dumps(payload).decode())


async def subscribe(channel: str) -> AsyncIterator[dict[str, Any]]:
    pubsub = get_redis().pubsub()
    await pubsub.subscribe(channel)
    try:
        async for msg in pubsub.listen():
            if msg.get("type") != "message":
                continue
            data = msg.get("data")
            if isinstance(data, str):
                yield orjson.loads(data)
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
