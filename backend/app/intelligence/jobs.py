"""Durable scheduled acquisition jobs for the intelligence control plane."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select

from app.db import SessionLocal
from app.intelligence.service import collect_source
from app.models.intelligence import CollectionSource, CollectionSubscription
from app.models.user import User
from app.schemas.intelligence import CollectionRequest
from app.telemetry.logging import get_logger

log = get_logger(__name__)
_BATCH_SIZE = 20


async def _claim_due_subscriptions() -> list[UUID]:
    """Atomically lease due subscriptions before making network requests."""
    now = datetime.now(UTC)
    async with SessionLocal() as db:
        rows = (
            await db.execute(
                select(CollectionSubscription, CollectionSource)
                .join(
                    CollectionSource,
                    CollectionSource.id == CollectionSubscription.collection_source_id,
                )
                .where(
                    CollectionSubscription.status == "active",
                    CollectionSubscription.next_due_at <= now,
                    CollectionSource.status == "active",
                )
                .order_by(CollectionSubscription.next_due_at)
                .limit(_BATCH_SIZE)
                .with_for_update(of=CollectionSubscription, skip_locked=True)
            )
        ).all()
        claimed: list[UUID] = []
        for subscription, source in rows:
            subscription.next_due_at = now + timedelta(minutes=source.schedule_minutes)
            claimed.append(subscription.id)
        await db.commit()
        return claimed


async def _record_failure(subscription_id: UUID, message: str) -> None:
    async with SessionLocal() as db:
        subscription = await db.get(CollectionSubscription, subscription_id)
        if not subscription:
            return
        source = await db.get(CollectionSource, subscription.collection_source_id)
        base_interval = source.schedule_minutes if source else 15
        subscription.consecutive_failures += 1
        backoff = min(
            base_interval * (2 ** min(subscription.consecutive_failures, 4)),
            1440,
        )
        subscription.next_due_at = datetime.now(UTC) + timedelta(minutes=backoff)
        subscription.last_error = message[:500]
        await db.commit()


async def _run_subscription(subscription_id: UUID) -> bool:
    async with SessionLocal() as db:
        subscription = await db.get(CollectionSubscription, subscription_id)
        if not subscription or subscription.status != "active":
            return False
        actor = await db.get(User, subscription.created_by) if subscription.created_by else None
        if not actor or actor.role not in {"admin", "superadmin"}:
            await _record_failure(
                subscription_id,
                "Monitoring authorization is no longer held by an active administrator",
            )
            return False
        try:
            await collect_source(
                db,
                actor,
                subscription.collection_source_id,
                CollectionRequest(
                    subject_id=subscription.subject_id,
                    path=subscription.path,
                    css_selector=subscription.css_selector,
                    language=subscription.language,
                    event_type=subscription.event_type,
                ),
            )
            subscription.last_collected_at = datetime.now(UTC)
            subscription.last_error = None
            subscription.consecutive_failures = 0
            await db.commit()
            return True
        except HTTPException as exc:
            await db.rollback()
            await _record_failure(subscription_id, str(exc.detail))
            return False
        except Exception as exc:
            await db.rollback()
            log.exception(
                "intelligence.collection.failed",
                subscription_id=str(subscription_id),
                error_type=type(exc).__name__,
            )
            await _record_failure(subscription_id, "Unexpected connector failure")
            return False


async def run_due_collections(ctx: dict[Any, Any]) -> int:
    """ARQ cron entrypoint; returns the number of successful acquisitions."""
    del ctx
    claimed = await _claim_due_subscriptions()
    completed = 0
    for subscription_id in claimed:
        completed += int(await _run_subscription(subscription_id))
    if claimed:
        log.info(
            "intelligence.collection.batch",
            claimed=len(claimed),
            completed=completed,
        )
    return completed
