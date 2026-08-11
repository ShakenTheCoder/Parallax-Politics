"""Application service hiding intelligence policy, persistence, and estimates."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urljoin, urlparse
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.intelligence.collector import SafePublicWebCollector
from app.intelligence.policy import (
    CollectionPolicyError,
    enforce_cohort_privacy,
    enforce_same_source,
    validate_public_destination,
)
from app.intelligence.population import (
    EvidenceObservation,
    population_response_provider,
)
from app.models.intelligence import (
    CollectionSource,
    CollectionSubscription,
    IntelligenceAuditEvent,
    IntelligenceScenario,
    SignalEvent,
    StrategyVerdict,
)
from app.models.profile import Profile
from app.models.source import Source
from app.models.user import User
from app.schemas.intelligence import (
    CollectionRequest,
    CollectionResult,
    CollectionSourceCreate,
    CollectionSourceOut,
    CollectionSubscriptionCreate,
    CollectionSubscriptionOut,
    IntelligenceOverview,
    PresenceMetric,
    ScenarioCreate,
    ScenarioOut,
    SignalOut,
    VerdictOut,
)


def _source_out(row: CollectionSource) -> CollectionSourceOut:
    return CollectionSourceOut(
        id=row.id,
        name=row.name,
        base_url=row.base_url,
        authority=row.authority,
        connector_kind=row.connector_kind,
        status=row.status,
        schedule_minutes=row.schedule_minutes,
        robots_observed=row.robots_observed,
        allowed_paths=list(row.allowed_paths or []),
        last_collected_at=row.last_collected_at,
    )


def _signal_out(row: SignalEvent) -> SignalOut:
    return SignalOut(
        id=row.id,
        subject_id=row.subject_id,
        platform=row.platform,
        event_type=row.event_type,
        language=row.language,
        title=row.title,
        content_excerpt=row.content[:500],
        url=row.url,
        published_at=row.published_at,
        observed_at=row.observed_at,
        engagement=dict(row.engagement or {}),
        provenance=dict(row.provenance or {}),
    )


def _subscription_out(row: CollectionSubscription) -> CollectionSubscriptionOut:
    return CollectionSubscriptionOut(
        id=row.id,
        collection_source_id=row.collection_source_id,
        subject_id=row.subject_id,
        path=row.path,
        language=row.language,
        event_type=row.event_type,
        status=row.status,
        next_due_at=row.next_due_at,
        last_collected_at=row.last_collected_at,
        last_error=row.last_error,
        consecutive_failures=row.consecutive_failures,
    )


def _scenario_out(row: IntelligenceScenario) -> ScenarioOut:
    return ScenarioOut(
        id=row.id,
        subject_id=row.subject_id,
        title=row.title,
        narrative=row.narrative,
        proposed_action=row.proposed_action,
        cohort=dict(row.cohort or {}),
        effective_at=row.effective_at,
        status=row.status,
        forecast=dict(row.forecast or {}),
        assumptions=list(row.assumptions or []),
        evidence=list(row.evidence or []),
        model_version=row.model_version,
        created_at=row.created_at,
    )


def _verdict_out(row: StrategyVerdict) -> VerdictOut:
    return VerdictOut(
        id=row.id,
        scenario_id=row.scenario_id,
        status=row.status,
        recommendation=row.recommendation,
        rationale=row.rationale,
        confidence=row.confidence,
        risk_level=row.risk_level,
        critic=dict(row.critic or {}),
        evidence=list(row.evidence or []),
        expires_at=row.expires_at,
        approved_by=row.approved_by,
        approved_at=row.approved_at,
        created_at=row.created_at,
    )


async def _audit(
    db: AsyncSession,
    *,
    actor: User,
    action: str,
    resource_type: str,
    resource_id: UUID | None,
    purpose: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    db.add(
        IntelligenceAuditEvent(
            actor_id=actor.id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            purpose=purpose,
            audit_metadata=metadata or {},
            occurred_at=datetime.now(UTC),
        )
    )


async def resolve_subject(db: AsyncSession, user: User, requested: UUID | None) -> Profile:
    subject_id = requested if user.role in {"admin", "superadmin"} else user.principal_id
    if not subject_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No authorized candidate is linked"
        )
    if user.role not in {"admin", "superadmin"} and requested and requested != user.principal_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Candidate access denied")
    profile = await db.get(Profile, subject_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    return profile


async def create_collection_source(
    db: AsyncSession, actor: User, payload: CollectionSourceCreate
) -> CollectionSourceOut:
    base_url = str(payload.base_url).rstrip("/")
    try:
        await validate_public_destination(base_url)
    except CollectionPolicyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    existing = (
        await db.execute(select(CollectionSource).where(CollectionSource.base_url == base_url))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Collection source already registered"
        )
    row = CollectionSource(
        name=payload.name,
        base_url=base_url,
        connector_kind=payload.connector_kind,
        authority=payload.authority.value,
        status="active",
        schedule_minutes=payload.schedule_minutes,
        robots_observed=payload.robots_observed,
        allowed_paths=payload.allowed_paths,
        source_metadata={"policy_version": "public-collection-v1"},
        created_by=actor.id,
    )
    db.add(row)
    await db.flush()
    await _audit(
        db,
        actor=actor,
        action="collection_source.created",
        resource_type="collection_source",
        resource_id=row.id,
        purpose="Configure authorized public intelligence source",
    )
    await db.commit()
    return _source_out(row)


async def list_collection_sources(db: AsyncSession) -> list[CollectionSourceOut]:
    rows = (
        (await db.execute(select(CollectionSource).order_by(CollectionSource.name))).scalars().all()
    )
    return [_source_out(row) for row in rows]


async def create_collection_subscription(
    db: AsyncSession,
    actor: User,
    source_id: UUID,
    payload: CollectionSubscriptionCreate,
) -> CollectionSubscriptionOut:
    source_cfg = await db.get(CollectionSource, source_id)
    if not source_cfg or source_cfg.status != "active":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active collection source not found",
        )
    if source_cfg.connector_kind != "scrapling":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This source requires its licensed connector",
        )
    await resolve_subject(db, actor, payload.subject_id)
    target = urljoin(source_cfg.base_url.rstrip("/") + "/", payload.path.lstrip("/"))
    try:
        enforce_same_source(target, source_cfg.base_url, list(source_cfg.allowed_paths or []))
    except CollectionPolicyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    existing = (
        await db.execute(
            select(CollectionSubscription).where(
                CollectionSubscription.collection_source_id == source_id,
                CollectionSubscription.subject_id == payload.subject_id,
                CollectionSubscription.path == payload.path,
            )
        )
    ).scalar_one_or_none()
    if existing:
        existing.status = "active"
        existing.css_selector = payload.css_selector
        existing.language = payload.language
        existing.event_type = payload.event_type
        existing.next_due_at = datetime.now(UTC) + timedelta(minutes=source_cfg.schedule_minutes)
        await db.commit()
        return _subscription_out(existing)

    row = CollectionSubscription(
        collection_source_id=source_id,
        subject_id=payload.subject_id,
        path=payload.path,
        css_selector=payload.css_selector,
        language=payload.language,
        event_type=payload.event_type,
        status="active",
        next_due_at=datetime.now(UTC) + timedelta(minutes=source_cfg.schedule_minutes),
        created_by=actor.id,
    )
    db.add(row)
    await db.flush()
    await _audit(
        db,
        actor=actor,
        action="collection_subscription.created",
        resource_type="collection_subscription",
        resource_id=row.id,
        purpose="Schedule authorized public evidence monitoring",
        metadata={"source_id": str(source_id), "subject_id": str(payload.subject_id)},
    )
    await db.commit()
    return _subscription_out(row)


async def list_collection_subscriptions(
    db: AsyncSession,
) -> list[CollectionSubscriptionOut]:
    rows = (
        (
            await db.execute(
                select(CollectionSubscription)
                .order_by(CollectionSubscription.created_at.desc())
                .limit(500)
            )
        )
        .scalars()
        .all()
    )
    return [_subscription_out(row) for row in rows]


async def collect_source(
    db: AsyncSession,
    actor: User,
    source_id: UUID,
    payload: CollectionRequest,
) -> CollectionResult:
    source_cfg = await db.get(CollectionSource, source_id)
    if not source_cfg or source_cfg.status != "active":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Active collection source not found"
        )
    if source_cfg.connector_kind != "scrapling":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This source requires its licensed connector",
        )
    if payload.subject_id:
        await resolve_subject(db, actor, payload.subject_id)
    try:
        document = await SafePublicWebCollector().collect(
            base_url=source_cfg.base_url,
            path=payload.path,
            allowed_paths=list(source_cfg.allowed_paths or []),
            robots_observed=source_cfg.robots_observed,
            css_selector=payload.css_selector,
        )
    except (CollectionPolicyError, httpx.HTTPError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    duplicate = (
        await db.execute(
            select(SignalEvent).where(
                SignalEvent.subject_id == payload.subject_id,
                SignalEvent.content_hash == document.content_hash,
            )
        )
    ).scalar_one_or_none()
    if duplicate:
        now = datetime.now(UTC)
        source_cfg.last_collected_at = now
        await _audit(
            db,
            actor=actor,
            action="signal.observed_duplicate",
            resource_type="signal",
            resource_id=duplicate.id,
            purpose="Confirm freshness of authorized public evidence",
            metadata={"source_id": str(source_cfg.id)},
        )
        await db.commit()
        return CollectionResult(created=False, signal=_signal_out(duplicate))

    domain = urlparse(document.url).hostname or "unknown"
    source_row = (
        await db.execute(select(Source).where(Source.url == document.url))
    ).scalar_one_or_none()
    if not source_row:
        credibility = 0.9 if source_cfg.authority == "official_api" else 0.7
        source_row = Source(
            url=document.url,
            domain=domain,
            title=document.title,
            excerpt=document.text[:1000],
            credibility_score=credibility,
            content_hash=document.content_hash,
            extra={"authority": source_cfg.authority, "collection_source_id": str(source_cfg.id)},
        )
        db.add(source_row)
        await db.flush()

    now = datetime.now(UTC)
    signal = SignalEvent(
        subject_id=payload.subject_id,
        collection_source_id=source_cfg.id,
        source_id=source_row.id,
        platform=domain,
        event_type=payload.event_type,
        language=payload.language,
        title=document.title,
        content=document.text,
        url=document.url,
        observed_at=now,
        engagement={},
        geography={},
        provenance={
            "authority": source_cfg.authority,
            "collector": "scrapling-parser/httpx-safe-fetch-v1",
            "content_type": document.content_type,
            "observed_at": now.isoformat(),
            "is_inference": False,
        },
        content_hash=document.content_hash,
        is_public=True,
    )
    db.add(signal)
    source_cfg.last_collected_at = now
    await db.flush()
    await _audit(
        db,
        actor=actor,
        action="signal.collected",
        resource_type="signal",
        resource_id=signal.id,
        purpose="Collect authorized public evidence",
        metadata={
            "source_id": str(source_cfg.id),
            "subject_id": str(payload.subject_id) if payload.subject_id else None,
        },
    )
    await db.commit()
    return CollectionResult(created=True, signal=_signal_out(signal))


async def intelligence_overview(db: AsyncSession, user: User) -> IntelligenceOverview:
    subject_filter = None if user.role in {"admin", "superadmin"} else user.principal_id
    if user.role not in {"admin", "superadmin"} and not subject_filter:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No authorized candidate is linked"
        )
    cutoff = datetime.now(UTC) - timedelta(hours=24)
    stmt = select(SignalEvent).where(SignalEvent.observed_at >= cutoff)
    if subject_filter:
        stmt = stmt.where(SignalEvent.subject_id == subject_filter)
    signals = (
        (await db.execute(stmt.order_by(SignalEvent.observed_at.desc()).limit(1000)))
        .scalars()
        .all()
    )

    profiles = (await db.execute(select(Profile))).scalars().all()
    profile_map = {profile.id: profile for profile in profiles}
    grouped: dict[UUID, list[SignalEvent]] = {}
    for signal in signals:
        if signal.subject_id:
            grouped.setdefault(signal.subject_id, []).append(signal)
    total_signals = sum(len(items) for items in grouped.values()) or 1
    presence: list[PresenceMetric] = []
    for subject_id, items in grouped.items():
        profile = profile_map.get(subject_id)
        if not profile:
            continue
        engagement_total = sum(
            int(value)
            for item in items
            for value in (item.engagement or {}).values()
            if isinstance(value, (int, float)) and value >= 0
        )
        presence.append(
            PresenceMetric(
                subject_id=subject_id,
                full_name=profile.full_name,
                signal_count=len(items),
                engagement_total=engagement_total,
                share_of_voice_pct=round(len(items) / total_signals * 100, 1),
                latest_signal_at=max(item.observed_at for item in items),
            )
        )
    presence.sort(key=lambda item: (item.signal_count, item.engagement_total), reverse=True)
    latest = max((signal.observed_at for signal in signals), default=None)
    freshness = int((datetime.now(UTC) - latest).total_seconds() / 60) if latest else None
    sources_active = int(
        (
            await db.execute(
                select(func.count())
                .select_from(CollectionSource)
                .where(CollectionSource.status == "active")
            )
        ).scalar_one()
    )
    pending_stmt = (
        select(func.count()).select_from(StrategyVerdict).where(StrategyVerdict.status == "draft")
    )
    if subject_filter:
        pending_stmt = pending_stmt.join(IntelligenceScenario).where(
            IntelligenceScenario.subject_id == subject_filter
        )
    pending = int((await db.execute(pending_stmt)).scalar_one())
    return IntelligenceOverview(
        generated_at=datetime.now(UTC),
        freshness_minutes=freshness,
        monitored_candidates=len(grouped),
        signals_24h=len(signals),
        sources_active=sources_active,
        scenarios_pending_review=pending,
        presence=presence,
        recent_signals=[_signal_out(row) for row in signals[:20]],
        data_notice="Online signals are observational and non-representative until calibrated against polling and consented panel evidence.",
    )


async def create_scenario(
    db: AsyncSession, actor: User, payload: ScenarioCreate
) -> tuple[ScenarioOut, VerdictOut]:
    try:
        enforce_cohort_privacy(payload.cohort.sample_size)
    except CollectionPolicyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    profile = await resolve_subject(db, actor, payload.subject_id)
    effective_at = payload.effective_at or datetime.now(UTC)
    if effective_at > datetime.now(UTC) + timedelta(minutes=5):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="effective_at cannot be in the future",
        )
    window_start = effective_at - timedelta(days=30)
    signals = (
        (
            await db.execute(
                select(SignalEvent)
                .where(SignalEvent.subject_id == profile.id)
                .where(SignalEvent.observed_at >= window_start)
                .where(SignalEvent.observed_at <= effective_at)
                .order_by(SignalEvent.observed_at.desc())
                .limit(500)
            )
        )
        .scalars()
        .all()
    )
    evidence = [
        {
            "signal_id": str(item.id),
            "url": item.url,
            "title": item.title,
            "observed_at": item.observed_at.isoformat(),
            "authority": (item.provenance or {}).get("authority"),
        }
        for item in signals[:12]
    ]
    estimate = population_response_provider.estimate(
        [
            EvidenceObservation(
                content=item.content,
                authority=(item.provenance or {}).get("authority"),
            )
            for item in signals
        ],
        evaluated_at=datetime.now(UTC),
    )
    forecast = estimate.forecast
    assumptions = estimate.assumptions
    representative = bool(forecast["representative_calibration"])
    confidence = float(forecast["confidence"])
    direction = str(forecast["direction"])
    scenario = IntelligenceScenario(
        subject_id=profile.id,
        created_by=actor.id,
        title=payload.title,
        narrative=payload.narrative,
        proposed_action=payload.proposed_action,
        cohort=payload.cohort.model_dump(),
        effective_at=effective_at,
        status="awaiting_analyst_review",
        forecast=forecast,
        assumptions=assumptions,
        evidence=evidence,
        model_version=estimate.model_version,
    )
    db.add(scenario)
    await db.flush()

    if direction == "insufficient_evidence":
        recommendation = "Do not issue a strategic verdict yet; collect representative polling or panel evidence for this cohort."
        risk_level = "high"
    elif direction == "negative":
        recommendation = "Do not proceed unchanged; revise the public framing and validate the alternative with a representative pre-test."
        risk_level = "high"
    elif direction == "positive":
        recommendation = "Consider a limited, measurable public test before broader use, with pre-defined stop conditions and post-test polling."
        risk_level = "medium"
    else:
        recommendation = "Treat the response as unresolved; compare two clearly differentiated public framings in a representative pre-test."
        risk_level = "medium"
    critic = {
        "decision": "requires_human_review",
        "primary_limitations": [
            "Observed association does not establish causality.",
            "Online discussion may overrepresent highly active users.",
            "Lexical signals may miss sarcasm, context, and code-switching.",
        ],
        "abstained": direction == "insufficient_evidence",
    }
    verdict = StrategyVerdict(
        scenario_id=scenario.id,
        status="draft",
        recommendation=recommendation,
        rationale=f"Draft based on {len(signals)} time-bounded signals; representative calibration: {'present' if representative else 'absent'}.",
        confidence=round(confidence, 3),
        risk_level=risk_level,
        critic=critic,
        evidence=evidence,
        expires_at=datetime.now(UTC) + timedelta(hours=24),
    )
    db.add(verdict)
    await db.flush()
    await _audit(
        db,
        actor=actor,
        action="scenario.created",
        resource_type="scenario",
        resource_id=scenario.id,
        purpose="Generate aggregate campaign-planning scenario",
        metadata={"subject_id": str(profile.id), "cohort_size": payload.cohort.sample_size},
    )
    await db.commit()
    return _scenario_out(scenario), _verdict_out(verdict)


async def list_scenarios(db: AsyncSession, user: User) -> list[ScenarioOut]:
    stmt = select(IntelligenceScenario).order_by(IntelligenceScenario.created_at.desc()).limit(100)
    if user.role not in {"admin", "superadmin"}:
        if not user.principal_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="No authorized candidate is linked"
            )
        stmt = stmt.where(IntelligenceScenario.subject_id == user.principal_id)
    rows = (await db.execute(stmt)).scalars().all()
    return [_scenario_out(row) for row in rows]


async def list_verdicts(db: AsyncSession, user: User) -> list[VerdictOut]:
    stmt = (
        select(StrategyVerdict)
        .join(IntelligenceScenario)
        .order_by(StrategyVerdict.created_at.desc())
        .limit(100)
    )
    if user.role not in {"admin", "superadmin"}:
        if not user.principal_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="No authorized candidate is linked"
            )
        stmt = stmt.where(IntelligenceScenario.subject_id == user.principal_id)
    rows = (await db.execute(stmt)).scalars().all()
    return [_verdict_out(row) for row in rows]


async def decide_verdict(
    db: AsyncSession,
    actor: User,
    verdict_id: UUID,
    decision: str,
    review_note: str,
) -> VerdictOut:
    verdict = await db.get(StrategyVerdict, verdict_id)
    if not verdict:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verdict not found")
    if verdict.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Verdict was already reviewed"
        )
    verdict.status = decision
    verdict.approved_by = actor.id
    verdict.approved_at = datetime.now(UTC)
    verdict.critic = {**(verdict.critic or {}), "analyst_review_note": review_note}
    scenario = await db.get(IntelligenceScenario, verdict.scenario_id)
    if scenario:
        scenario.status = decision
    await _audit(
        db,
        actor=actor,
        action=f"verdict.{decision}",
        resource_type="verdict",
        resource_id=verdict.id,
        purpose="Authorized analyst review",
        metadata={"review_note": review_note},
    )
    await db.flush()
    await db.commit()
    return _verdict_out(verdict)
