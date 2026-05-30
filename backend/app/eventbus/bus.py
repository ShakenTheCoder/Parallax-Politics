"""Thin pub/sub helpers used by agents + orchestrator + SSE endpoints."""
from collections.abc import AsyncIterator
from typing import Any

from app.redis import publish, subscribe


async def publish_event(channel: str, payload: dict[str, Any]) -> int:
    return await publish(channel, payload)


async def stream_events(channel: str) -> AsyncIterator[dict[str, Any]]:
    async for event in subscribe(channel):
        yield event
