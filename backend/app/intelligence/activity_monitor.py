"""Glossary-wide public activity monitoring and normalized activity projection."""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.intelligence.activity_sources import bootstrap_activity_sources
from app.intelligence.brief_watchlist import normalize_public_name, public_name_keys
from app.intelligence.collector import SafePublicWebCollector
from app.intelligence.rss import FeedItem, PublisherFeedCollector
from app.models.political_activity import PoliticalActivity, PoliticalActivitySource
from app.models.political_figure import PoliticalFigure
from app.schemas.intelligence import (
    ActivityWindow,
    PoliticalActivityCollectionOut,
    PoliticalActivityMonitorOut,
    PoliticalActivityOut,
    PoliticalActivityPersonOut,
    PoliticalActivitySourceOut,
)

_DIRECT_LAYERS = {"direct_appearance", "public_statement"}
_WINDOW_HOURS: dict[ActivityWindow, int] = {"6h": 6, "24h": 24, "7d": 168}
_MAX_DOCUMENT_CHARS = 6_000
_APPEARANCE_TYPES = {
    "speech_or_statement",
    "interview",
    "debate",
    "hearing_or_government_session",
    "press_conference",
    "public_event",
    "social_media_video",
    "written_statement",
    "official_announcement",
    "indirect_coverage",
    "public_reaction",
}
_PUBLISHER_STATEMENT_CUE = re.compile(
    r"\b(says?|said|states?|announces?|announced|calls?|called|urges?|urged|vows?|vowed|"
    r"warns?|warned|asks?|asked|tells?|told|denies?|denied|confirms?|confirmed|writes?|"
    r"wrote|posts?|posted|declares?|declared|highlights?|highlighted|extends?|extended|pushes?|pushed)\b",
    re.I,
)
_PUBLISHER_APPEARANCE_CUE = re.compile(
    r"\b(interview|debate|hearing|testif(?:y|ies|ied)|press conference|briefing|speech|"
    r"keynote|address|livestream|town hall)\b",
    re.I,
)


class ActivityExtraction(BaseModel):
    relevant: bool
    person_present: bool = False
    evidence_layer: Literal[
        "direct_appearance", "public_statement", "indirect_coverage", "public_reaction"
    ]
    appearance_type: str
    occurred_at: str | None = None
    venue_program: str | None = None
    topic: str = Field(min_length=2, max_length=240)
    summary: str = Field(min_length=10, max_length=600)
    claims: list[str] = Field(default_factory=list, max_length=8)
    self_initiated: bool = False
    confidence: float = Field(ge=0, le=1)


class OllamaActivityAnalyzer:
    """Small provider seam; replace this adapter when hosted API access is enabled."""

    model_version = "activity-extraction-v1"

    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.ollama_activity_model
        self.timeout = settings.llm_request_timeout_seconds
        self.endpoint = settings.ollama_base_url.removesuffix("/v1").rstrip("/") + "/api/chat"

    async def analyze(
        self,
        *,
        figure: PoliticalFigure,
        source: PoliticalActivitySource,
        item: FeedItem,
    ) -> ActivityExtraction:
        aliases = [figure.canonical_name, *(figure.aliases or [])]
        prompt = (
            "Normalize one public political-activity source. An article about the person is NOT "
            "a direct appearance. Use direct_appearance only for an interview, speech, livestream, "
            "hearing, debate, press conference, or event where the person is present. Use "
            "public_statement for their own post, press release, written statement, announcement, "
            "or attributable recorded message. Use indirect_coverage when others discuss them, and "
            "public_reaction for measured/reported reaction to an event. Never infer facts missing "
            "from the source.\n\n"
            f"PERSON: {figure.canonical_name}\nALIASES: {aliases}\nROLE: {figure.current_role or ''}\n"
            f"SOURCE CLASS: {source.source_class}\nPUBLISHER: {source.publisher}\n"
            f"TITLE: {item.title}\nPUBLISHED: {item.published_at.isoformat() if item.published_at else 'unknown'}\n"
            f"TEXT: {(item.summary or item.title)[:_MAX_DOCUMENT_CHARS]}"
        )
        payload = {
            "model": self.model,
            "stream": False,
            "think": False,
            "format": ActivityExtraction.model_json_schema(),
            "messages": [
                {
                    "role": "system",
                    "content": "You are an evidence-conservative Philippine public-activity extractor. Return only the requested JSON schema.",
                },
                {"role": "user", "content": prompt},
            ],
            "options": {"temperature": 0, "num_predict": 500},
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.endpoint, json=payload)
            response.raise_for_status()
        body = response.json()
        content = ((body.get("message") or {}).get("content") or "").strip()
        try:
            result = ActivityExtraction.model_validate_json(content)
        except ValidationError as exc:
            raise RuntimeError("Ollama returned an invalid activity record") from exc
        return normalize_extraction(result)


@dataclass
class _Counters:
    sources_checked: int = 0
    entries_seen: int = 0
    activities_created: int = 0
    activities_merged: int = 0
    unmatched: int = 0
    errors: list[str] = field(default_factory=list)


def window_hours(window: ActivityWindow) -> int:
    return _WINDOW_HOURS[window]


def normalize_extraction(result: ActivityExtraction) -> ActivityExtraction:
    """Enforce layer/type invariants after schema validation."""
    if result.evidence_layer == "indirect_coverage":
        result.appearance_type = "indirect_coverage"
        result.person_present = False
        result.self_initiated = False
    elif result.evidence_layer == "public_reaction":
        result.appearance_type = "public_reaction"
        result.person_present = False
        result.self_initiated = False
    elif result.evidence_layer == "public_statement" and result.appearance_type in {
        "indirect_coverage",
        "public_reaction",
    }:
        result.appearance_type = "written_statement"
    elif result.appearance_type not in _APPEARANCE_TYPES:
        result.appearance_type = "speech_or_statement"
    return result


def enforce_publisher_evidence_layer(
    source: PoliticalActivitySource,
    figure: PoliticalFigure,
    item: FeedItem,
    result: ActivityExtraction,
) -> ActivityExtraction:
    """Prevent an LLM from upgrading ordinary publisher coverage into participation."""
    if source.source_class != "publisher" or result.evidence_layer in {
        "indirect_coverage",
        "public_reaction",
    }:
        return normalize_extraction(result)
    title = item.title.strip()
    cue = _PUBLISHER_STATEMENT_CUE.search(title)
    subject_terms = {
        normalize_public_name(value).split()[-1]
        for value in [figure.canonical_name, *(figure.aliases or [])]
        if normalize_public_name(value)
    }
    subject_positions = [
        match.start()
        for term in subject_terms
        if (match := re.search(rf"(?<!\w){re.escape(term)}(?!\w)", title, re.I))
    ]
    attributable_statement = bool(
        cue and subject_positions and min(subject_positions) < cue.start()
    )
    supported = (result.evidence_layer == "public_statement" and attributable_statement) or (
        result.evidence_layer == "direct_appearance"
        and result.person_present
        and bool(subject_positions)
        and bool(_PUBLISHER_APPEARANCE_CUE.search(title))
    )
    if not supported:
        result.evidence_layer = "indirect_coverage"
        result.appearance_type = "indirect_coverage"
        result.person_present = False
        result.self_initiated = False
    return normalize_extraction(result)


def monitoring_state(current_count: int, previous_count: int) -> str:
    if current_count >= 2 and (previous_count == 0 or current_count >= previous_count * 2):
        return "emerging"
    if current_count > 0:
        return "active"
    return "quiet"


def activity_change(current_count: int, previous_count: int) -> str:
    if current_count > previous_count:
        return "up"
    if current_count < previous_count:
        return "down"
    return "steady"


def _aliases(figure: PoliticalFigure) -> tuple[str, ...]:
    values = public_name_keys(figure)
    return tuple(
        sorted(
            (value for value in values if len(value.split()) >= 2),
            key=len,
            reverse=True,
        )
    )


def _matches(item: FeedItem, figure: PoliticalFigure) -> bool:
    text = normalize_public_name(f"{item.title} {item.summary}")
    return any(re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", text) for alias in _aliases(figure))


def _identity_basis(
    source: PoliticalActivitySource, figure: PoliticalFigure
) -> tuple[float, dict[str, Any]]:
    if source.figure_id == figure.id:
        return 0.98, {"method": "verified_official_source", "face_recognition": False}
    return 0.82, {
        "method": "exact_name_or_alias_with_source_context",
        "aliases": list(_aliases(figure)),
        "face_recognition": False,
    }


def _confidence(source: PoliticalActivitySource, identity: float, extraction: float) -> float:
    source_score = 0.95 if source.reliability_tier == "primary" else 0.78
    return round(min(0.99, source_score * 0.4 + identity * 0.35 + extraction * 0.25), 3)


def _parse_occurred_at(value: str | None, fallback: datetime | None, now: datetime) -> datetime:
    if value:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            if parsed <= now + timedelta(hours=12):
                return parsed
        except ValueError:
            pass
    return fallback or now


def _tokens(value: str | None) -> set[str]:
    return {token for token in normalize_public_name(value or "").split() if len(token) >= 4}


def _similar(left: PoliticalActivity, extraction: ActivityExtraction) -> bool:
    if left.appearance_type != extraction.appearance_type:
        return False
    left_tokens = _tokens(f"{left.topic} {left.venue_program or ''}")
    right_tokens = _tokens(f"{extraction.topic} {extraction.venue_program or ''}")
    if not left_tokens or not right_tokens:
        return False
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens) >= 0.45


def _cluster_key(
    figure: PoliticalFigure, extraction: ActivityExtraction, occurred_at: datetime
) -> str:
    normalized = "|".join(
        (
            str(figure.id),
            occurred_at.date().isoformat(),
            extraction.appearance_type,
            " ".join(sorted(_tokens(extraction.topic))),
            " ".join(sorted(_tokens(extraction.venue_program))),
        )
    )
    return hashlib.sha256(normalized.encode()).hexdigest()


async def _save_activity(
    db: AsyncSession,
    *,
    source: PoliticalActivitySource,
    figure: PoliticalFigure,
    item: FeedItem,
    extraction: ActivityExtraction,
    now: datetime,
    analyzer: OllamaActivityAnalyzer,
) -> Literal["created", "merged", "ignored"]:
    if not extraction.relevant:
        return "ignored"
    occurred_at = _parse_occurred_at(extraction.occurred_at, item.published_at, now)
    identity_score, identity_basis = _identity_basis(source, figure)
    confidence = _confidence(source, identity_score, extraction.confidence)
    source_text = normalize_public_name(f"{item.title} {item.summary}")
    grounded_claims = [
        claim[:500]
        for claim in extraction.claims
        if len(normalize_public_name(claim)) >= 8 and normalize_public_name(claim) in source_text
    ]
    link = {
        "url": item.url,
        "title": item.title,
        "publisher": source.publisher,
        "published_at": item.published_at.isoformat() if item.published_at else None,
        "source_class": source.source_class,
    }
    candidates = list(
        (
            await db.execute(
                select(PoliticalActivity).where(
                    PoliticalActivity.figure_id == figure.id,
                    PoliticalActivity.occurred_at >= occurred_at - timedelta(hours=18),
                    PoliticalActivity.occurred_at <= occurred_at + timedelta(hours=18),
                )
            )
        )
        .scalars()
        .all()
    )
    duplicate = next(
        (
            row
            for row in candidates
            if row.content_hash == item.content_hash
            or row.direct_source_url == item.url
            or _similar(row, extraction)
        ),
        None,
    )
    if duplicate:
        links = list(duplicate.source_links or [])
        if not any(existing.get("url") == item.url for existing in links):
            links.append(link)
            duplicate.source_links = links
            duplicate.evidence_confidence = min(
                0.99, round(duplicate.evidence_confidence + 0.04, 3)
            )
        return "merged"

    layer = extraction.evidence_layer
    initiation = (
        "self_initiated"
        if extraction.self_initiated and layer in _DIRECT_LAYERS
        else "earned_appearance"
        if layer == "direct_appearance"
        else "publisher_coverage"
    )
    db.add(
        PoliticalActivity(
            created_at=now,
            updated_at=now,
            figure_id=figure.id,
            primary_source_id=source.id,
            occurred_at=occurred_at,
            published_at=item.published_at,
            appearance_type=extraction.appearance_type,
            evidence_layer=layer,
            initiation=initiation,
            venue_program=extraction.venue_program,
            topic=extraction.topic.strip(),
            summary=extraction.summary.strip(),
            direct_source_url=item.url,
            publisher=source.publisher,
            evidence_confidence=confidence,
            confidence_basis={
                "source_quality": source.reliability_tier,
                "identity_confidence": identity_score,
                "extractor_confidence": extraction.confidence,
                "source_overlap": 1,
                "grounded_claims": len(grounded_claims),
                "discarded_ungrounded_claims": len(extraction.claims) - len(grounded_claims),
            },
            identity_basis=identity_basis,
            geography={"scope": "Philippines", "basis": "source_catalog"},
            claims=grounded_claims,
            source_links=[link],
            content_hash=item.content_hash,
            cluster_key=_cluster_key(figure, extraction, occurred_at),
            analyzer="ollama_structured_output",
            model_version=f"{analyzer.model_version}:{analyzer.model}",
            review_status="machine_reviewed",
        )
    )
    return "created"


async def _items_for_source(source: PoliticalActivitySource) -> list[FeedItem]:
    settings = get_settings()
    if source.access_method in {"rss", "youtube_atom"}:
        return await PublisherFeedCollector().collect(
            source.url,
            max_items=(
                settings.free_youtube_max_items_per_feed
                if source.access_method == "youtube_atom"
                else settings.free_rss_max_items_per_feed
            ),
            timeout_seconds=settings.free_rss_request_timeout_seconds,
        )
    if source.access_method == "scrapling":
        parsed = urlparse(source.url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        document = await SafePublicWebCollector().collect(
            base_url=base_url,
            path=parsed.path or "/",
            allowed_paths=[
                str((source.source_metadata or {}).get("allowed_path") or parsed.path or "/")
            ],
            robots_observed=source.robots_observed,
        )
        return [
            FeedItem(
                external_id=document.content_hash,
                title=document.title or source.name,
                summary=document.text,
                url=document.url,
                published_at=None,
                content_hash=document.content_hash,
            )
        ]
    return []


async def collect_political_activity(
    db: AsyncSession,
    *,
    analyzer: OllamaActivityAnalyzer | None = None,
    max_analyses: int | None = None,
) -> PoliticalActivityCollectionOut:
    """Collect active allowlisted sources and normalize matched evidence through Ollama."""

    settings = get_settings()
    if settings.llm_provider != "ollama":
        return PoliticalActivityCollectionOut(
            errors=["Political activity ingestion requires LLM_PROVIDER=ollama in this phase"]
        )
    sources = await bootstrap_activity_sources(db)
    figures = list(
        (await db.execute(select(PoliticalFigure).where(PoliticalFigure.archived_at.is_(None))))
        .scalars()
        .all()
    )
    figure_by_id = {figure.id: figure for figure in figures}
    analyzer = analyzer or OllamaActivityAnalyzer()
    counters = _Counters()
    now = datetime.now(UTC)
    analyzed = 0
    analysis_limit = max_analyses or settings.political_activity_max_llm_items_per_run

    for source in (item for item in sources if item.status == "active"):
        try:
            items = await _items_for_source(source)
            source.last_error = None
        except Exception as exc:
            source.last_error = f"{type(exc).__name__}: {str(exc)[:420]}"
            source.last_checked_at = now
            if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in {
                401,
                403,
                429,
            }:
                source.status = "blocked"
            elif "robots" in str(exc).casefold():
                source.status = "needs_review"
            counters.errors.append(f"{source.name}: {type(exc).__name__}")
            continue
        counters.sources_checked += 1
        counters.entries_seen += len(items)
        source.last_checked_at = now
        for item in items:
            if item.published_at and item.published_at < now - timedelta(days=8):
                continue
            candidates = (
                [figure_by_id[source.figure_id]]
                if source.figure_id in figure_by_id
                else [figure for figure in figures if _matches(item, figure)]
            )
            if not candidates:
                counters.unmatched += 1
                continue
            for figure in candidates:
                existing = (
                    await db.execute(
                        select(PoliticalActivity.id).where(
                            PoliticalActivity.figure_id == figure.id,
                            PoliticalActivity.content_hash == item.content_hash,
                        )
                    )
                ).scalar_one_or_none()
                if existing:
                    counters.activities_merged += 1
                    continue
                if analyzed >= analysis_limit:
                    counters.errors.append(
                        f"Analysis cap reached ({analysis_limit}); remaining matched items deferred"
                    )
                    await db.commit()
                    return PoliticalActivityCollectionOut(**vars(counters))
                try:
                    extraction = await analyzer.analyze(figure=figure, source=source, item=item)
                    analyzed += 1
                    extraction = enforce_publisher_evidence_layer(source, figure, item, extraction)
                    result = await _save_activity(
                        db,
                        source=source,
                        figure=figure,
                        item=item,
                        extraction=extraction,
                        now=now,
                        analyzer=analyzer,
                    )
                    counters.activities_created += int(result == "created")
                    counters.activities_merged += int(result == "merged")
                    counters.unmatched += int(result == "ignored")
                except Exception as exc:
                    counters.errors.append(
                        f"{source.name} / {figure.canonical_name}: {type(exc).__name__}"
                    )
        await db.flush()
        await db.commit()
    return PoliticalActivityCollectionOut(**vars(counters))


async def list_activity_sources(db: AsyncSession) -> list[PoliticalActivitySourceOut]:
    rows = list(
        (
            await db.execute(
                select(PoliticalActivitySource, PoliticalFigure)
                .outerjoin(PoliticalFigure, PoliticalFigure.id == PoliticalActivitySource.figure_id)
                .order_by(PoliticalActivitySource.source_class, PoliticalActivitySource.name)
            )
        ).all()
    )
    return [
        PoliticalActivitySourceOut(
            id=source.id,
            figure_id=source.figure_id,
            figure_name=figure.canonical_name if figure else None,
            name=source.name,
            url=source.url,
            source_class=source.source_class,
            platform=source.platform,
            access_method=source.access_method,
            publisher=source.publisher,
            status=source.status,
            schedule_minutes=source.schedule_minutes,
            rights=source.rights,
            reliability_tier=source.reliability_tier,
            last_checked_at=source.last_checked_at,
            last_error=source.last_error,
        )
        for source, figure in rows
    ]


def _confidence_label(values: list[float]) -> str:
    if not values:
        return "unavailable"
    average = sum(values) / len(values)
    if average >= 0.82:
        return "high"
    if average >= 0.65:
        return "medium"
    return "low"


def _activity_out(activity: PoliticalActivity, figure: PoliticalFigure) -> PoliticalActivityOut:
    return PoliticalActivityOut(
        id=activity.id,
        figure_id=figure.id,
        person=figure.canonical_name,
        portrait_url=figure.portrait_url,
        occurred_at=activity.occurred_at,
        published_at=activity.published_at,
        appearance_type=activity.appearance_type,
        evidence_layer=activity.evidence_layer,  # type: ignore[arg-type]
        initiation=activity.initiation,
        venue_program=activity.venue_program,
        topic=activity.topic,
        summary=activity.summary,
        direct_source_url=activity.direct_source_url,
        publisher=activity.publisher,
        evidence_confidence=activity.evidence_confidence,
        source_links=list(activity.source_links or []),
        geography=dict(activity.geography or {}),
    )


async def ollama_health() -> tuple[str, str]:
    settings = get_settings()
    if settings.llm_provider != "ollama":
        return settings.llm_provider, "misconfigured"
    endpoint = settings.ollama_base_url.removesuffix("/v1").rstrip("/") + "/api/tags"
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            response = await client.get(endpoint)
            response.raise_for_status()
        models = {item.get("name") for item in response.json().get("models", [])}
        return "ollama", "ready" if settings.ollama_activity_model in models else "model_missing"
    except Exception:
        return "ollama", "unavailable"


async def activity_monitor(
    db: AsyncSession, *, window: ActivityWindow
) -> PoliticalActivityMonitorOut:
    hours = window_hours(window)
    now = datetime.now(UTC)
    current_start = now - timedelta(hours=hours)
    previous_start = current_start - timedelta(hours=hours)
    figures = list(
        (
            await db.execute(
                select(PoliticalFigure)
                .where(PoliticalFigure.archived_at.is_(None))
                .order_by(PoliticalFigure.canonical_name)
            )
        )
        .scalars()
        .all()
    )
    sources = list((await db.execute(select(PoliticalActivitySource))).scalars().all())
    activities = list(
        (
            await db.execute(
                select(PoliticalActivity)
                .where(
                    PoliticalActivity.occurred_at >= previous_start,
                    PoliticalActivity.occurred_at <= now,
                )
                .order_by(PoliticalActivity.occurred_at.desc())
            )
        )
        .scalars()
        .all()
    )
    figure_index = {figure.id: figure for figure in figures}
    people: list[PoliticalActivityPersonOut] = []
    for figure in figures:
        rows = [row for row in activities if row.figure_id == figure.id]
        direct = [row for row in rows if row.evidence_layer in _DIRECT_LAYERS]
        current = [row for row in direct if row.occurred_at >= current_start]
        previous = [row for row in direct if row.occurred_at < current_start]
        topics = Counter(row.topic for row in current)
        publishers = Counter(
            str(link.get("publisher") or row.publisher)
            for row in current
            for link in (row.source_links or [{"publisher": row.publisher}])
        )
        strongest = [
            {"publisher": publisher, "records": count}
            for publisher, count in publishers.most_common(3)
        ]
        people.append(
            PoliticalActivityPersonOut(
                figure_id=figure.id,
                slug=figure.slug,
                person=figure.canonical_name,
                position=figure.current_role,
                portrait_url=figure.portrait_url,
                monitoring_state=monitoring_state(len(current), len(previous)),  # type: ignore[arg-type]
                last_appearance_at=max((row.occurred_at for row in direct), default=None),
                main_topic=topics.most_common(1)[0][0] if topics else None,
                current_count=len(current),
                previous_count=len(previous),
                activity_change=activity_change(len(current), len(previous)),  # type: ignore[arg-type]
                source_count=len(publishers),
                confidence_label=_confidence_label([row.evidence_confidence for row in current]),  # type: ignore[arg-type]
                strongest_sources=strongest,
            )
        )
    state_order = {"emerging": 0, "active": 1, "quiet": 2}
    people.sort(
        key=lambda row: (
            state_order[row.monitoring_state],
            -row.current_count,
            row.person,
        )
    )
    provider, provider_status = await ollama_health()
    return PoliticalActivityMonitorOut(
        window=window,
        window_hours=hours,
        generated_at=now,
        people_monitored=len(figures),
        active_sources=sum(source.status == "active" for source in sources),
        source_gaps=sum(source.status != "active" for source in sources),
        llm_provider=provider,
        llm_status=provider_status,
        people=people,
        recent_activity=[
            _activity_out(row, figure_index[row.figure_id])
            for row in activities
            if row.occurred_at >= current_start and row.figure_id in figure_index
        ][:100],
    )
