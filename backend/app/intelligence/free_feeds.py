"""Zero-credential publisher-feed ingestion and 36-hour media assessments."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse

import httpx
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.intelligence.appearance_classifier import classify_publisher_appearance
from app.intelligence.brief_watchlist import normalize_public_name, public_name_keys
from app.intelligence.official_youtube import collect_official_youtube_appearances
from app.intelligence.policy import CollectionPolicyError
from app.intelligence.rss import FeedItem, PublisherFeedCollector
from app.models.intelligence import CollectionSource, IntelligenceSnapshot, SignalEvent
from app.models.political_figure import PoliticalFigure
from app.models.profile import Profile
from app.models.source import Source
from app.models.user import User
from app.schemas.intelligence import CollectionSourceOut, FreeFeedCollectionOut

_WORD_SPACE = re.compile(r"\s+")
_MODEL_VERSION = "extractive-public-media-36h-v1"


@dataclass(frozen=True)
class FreeFeedDefinition:
    name: str
    url: str
    discovery_url: str
    language: str = "en"


@dataclass
class _Counters:
    feeds_checked: int = 0
    entries_seen: int = 0
    signals_created: int = 0
    duplicates: int = 0
    unmatched: int = 0
    appearances_created: int = 0
    opinions_created: int = 0
    errors: list[str] = field(default_factory=list)


DEFAULT_FREE_FEEDS = (
    FreeFeedDefinition(
        name="GMA News",
        url="https://data.gmanetwork.com/gno/rss/news/feed.xml",
        discovery_url="https://www.gmanetwork.com/news/rss/",
        language="en-fil",
    ),
    FreeFeedDefinition(
        name="GMA News Video",
        url="https://data.gmanetwork.com/gno/rss/video/feed.xml",
        discovery_url="https://www.gmanetwork.com/news/rss/",
        language="en-fil",
    ),
    FreeFeedDefinition(
        name="Philstar Headlines",
        url="https://www.philstar.com/rss/headlines",
        discovery_url="https://www.philstar.com/rss",
    ),
    FreeFeedDefinition(
        name="Philstar Nation",
        url="https://www.philstar.com/rss/nation",
        discovery_url="https://www.philstar.com/rss",
    ),
    FreeFeedDefinition(
        name="Inquirer NewsInfo",
        url="https://newsinfo.inquirer.net/feed",
        discovery_url="https://services.inquirer.net/",
    ),
    FreeFeedDefinition(
        name="Rappler",
        url="https://www.rappler.com/feed/",
        discovery_url="https://www.rappler.com/feed/",
    ),
    FreeFeedDefinition(
        name="Manila Times News",
        url="https://www.manilatimes.net/news/feed",
        discovery_url="https://www.manilatimes.net/news",
    ),
    FreeFeedDefinition(
        name="BusinessWorld",
        url="https://bworldonline.com/feed/",
        discovery_url="https://bworldonline.com/",
    ),
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


def _aliases(profile: Profile, figure: PoliticalFigure | None = None) -> tuple[str, ...]:
    raw: list[str] = [profile.full_name]
    identity_aliases = (profile.identity or {}).get("aliases", [])
    if isinstance(identity_aliases, list):
        raw.extend(str(alias) for alias in identity_aliases if alias)
    if figure:
        raw.extend([figure.canonical_name, *(figure.aliases or [])])
    terms = {_WORD_SPACE.sub(" ", alias).strip().casefold() for alias in raw}
    return tuple(sorted((term for term in terms if len(term) >= 4), key=len, reverse=True))


def _contains_alias(text: str, aliases: tuple[str, ...]) -> bool:
    haystack = text.casefold()
    return any(re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", haystack) for alias in aliases)


def _matches(item: FeedItem, aliases: tuple[str, ...]) -> bool:
    return _contains_alias(f"{item.title}\n{item.summary}", aliases)


def _importance(item_count: int, source_count: int) -> str:
    if item_count >= 8 and source_count >= 4:
        return "critical"
    if item_count >= 5 or source_count >= 3:
        return "high"
    if item_count >= 2:
        return "medium"
    return "low"


def _assessment_summary(signals: list[SignalEvent], aliases: tuple[str, ...] = ()) -> str:
    distinct_titles = list(dict.fromkeys(signal.title for signal in signals if signal.title))
    # A feed description can establish relevance even when the headline foregrounds
    # another person. Lead the digest with headlines naming the subject directly.
    direct_titles = [title for title in distinct_titles if _contains_alias(title, aliases)]
    titles = (direct_titles + [title for title in distinct_titles if title not in direct_titles])[
        :3
    ]
    source_count = len({signal.platform for signal in signals})
    focus = f"“{titles[0]}”" if len(titles) == 1 else "; ".join(f"“{title}”" for title in titles)
    return (
        f"Public coverage in the last 36 hours centers on {focus}. "
        f"This assessment is based on {len(signals)} attributed item"
        f"{'s' if len(signals) != 1 else ''} across {source_count} publisher"
        f"{'s' if source_count != 1 else ''}; it describes media attention, not public opinion."
    )


async def bootstrap_free_feeds(
    db: AsyncSession, actor: User | None = None
) -> list[CollectionSourceOut]:
    existing = {
        row.base_url: row
        for row in (
            (
                await db.execute(
                    select(CollectionSource).where(CollectionSource.connector_kind == "rss")
                )
            )
            .scalars()
            .all()
        )
    }
    rows: list[CollectionSource] = []
    for definition in DEFAULT_FREE_FEEDS:
        row = existing.get(definition.url.rstrip("/")) or existing.get(definition.url)
        if not row:
            row = CollectionSource(
                name=definition.name,
                base_url=definition.url,
                connector_kind="rss",
                authority="public_web",
                status="active",
                schedule_minutes=15,
                robots_observed=True,
                allowed_paths=[],
                source_metadata={
                    "policy_version": "publisher-rss-v1",
                    "discovery_url": definition.discovery_url,
                    "language": definition.language,
                    "source_rights": "headline_excerpt_link_only",
                },
                created_by=actor.id if actor else None,
            )
            db.add(row)
            await db.flush()
        rows.append(row)
    await db.commit()
    return [_source_out(row) for row in rows]


async def _source_record(db: AsyncSession, source: CollectionSource, item: FeedItem) -> Source:
    row = (await db.execute(select(Source).where(Source.url == item.url))).scalar_one_or_none()
    if row:
        return row
    domain = urlparse(item.url).hostname or "unknown"
    row = Source(
        url=item.url,
        domain=domain,
        title=item.title,
        excerpt=item.summary[:1000],
        published_at=item.published_at.isoformat() if item.published_at else None,
        credibility_score=0.75,
        content_hash=item.content_hash,
        extra={
            "authority": "publisher_rss",
            "collection_source_id": str(source.id),
            "rights": "headline_excerpt_link_only",
        },
    )
    db.add(row)
    await db.flush()
    return row


async def _create_assessments(
    db: AsyncSession,
    profiles: list[Profile],
    profile_aliases: dict[object, tuple[str, ...]],
) -> int:
    now = datetime.now(UTC)
    cutoff = now - timedelta(hours=36)
    created = 0
    for profile in profiles:
        signal_time = func.coalesce(SignalEvent.published_at, SignalEvent.observed_at)
        signals = (
            (
                await db.execute(
                    select(SignalEvent)
                    .where(
                        SignalEvent.subject_id == profile.id,
                        SignalEvent.event_type == "media_mention",
                        signal_time >= cutoff,
                        signal_time <= now,
                    )
                    .order_by(signal_time.desc())
                    .limit(100)
                )
            )
            .scalars()
            .all()
        )
        source_count = len({signal.platform for signal in signals})
        # One publisher mentioning a person is too little evidence for a media
        # assessment. Keep the empty state until two independent publishers agree
        # there is a current coverage theme.
        if len(signals) < 2 or source_count < 2:
            continue
        evidence = [
            {
                "signal_id": str(signal.id),
                "url": signal.url,
                "title": signal.title,
                "source": signal.platform,
                "published_at": (signal.published_at or signal.observed_at).isoformat(),
            }
            for signal in signals
        ]
        fingerprint = hashlib.sha256(
            "\n".join(sorted(item["signal_id"] for item in evidence)).encode()
        ).hexdigest()
        latest = (
            await db.execute(
                select(IntelligenceSnapshot)
                .where(
                    IntelligenceSnapshot.subject_id == profile.id,
                    IntelligenceSnapshot.kind == "media_opinion_36h",
                )
                .order_by(IntelligenceSnapshot.effective_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if latest and (latest.payload or {}).get("evidence_fingerprint") == fingerprint:
            continue
        # Preserve useful history without producing a new "opinion" every time a
        # feed republishes or updates a headline.
        if latest and now - latest.effective_at < timedelta(hours=1):
            continue
        db.add(
            IntelligenceSnapshot(
                subject_id=profile.id,
                kind="media_opinion_36h",
                scope_key="philippines:public-media:36h",
                window_start=cutoff,
                window_end=now,
                effective_at=now,
                payload={
                    "summary": _assessment_summary(signals, profile_aliases[profile.id]),
                    "importance": _importance(len(signals), source_count),
                    "item_count": len(signals),
                    "source_count": source_count,
                    "evidence_fingerprint": fingerprint,
                    "assessment_type": "extractive_media_attention",
                },
                evidence=evidence,
                produced_by="free-publisher-rss",
                model_version=_MODEL_VERSION,
                confidence=min(0.9, 0.45 + source_count * 0.1),
            )
        )
        created += 1
    return created


async def collect_free_feeds(db: AsyncSession, actor: User | None = None) -> FreeFeedCollectionOut:
    settings = get_settings()
    if not settings.free_rss_enabled:
        return FreeFeedCollectionOut(errors=["Free RSS acquisition is disabled"])
    await bootstrap_free_feeds(db, actor)
    sources = (
        (
            await db.execute(
                select(CollectionSource)
                .where(
                    CollectionSource.connector_kind == "rss",
                    CollectionSource.status == "active",
                )
                .order_by(CollectionSource.name)
            )
        )
        .scalars()
        .all()
    )
    profiles = list((await db.execute(select(Profile))).scalars().all())
    figures = list(
        (await db.execute(select(PoliticalFigure).where(PoliticalFigure.archived_at.is_(None))))
        .scalars()
        .all()
    )
    figure_index = {key: figure for figure in figures for key in public_name_keys(figure)}
    profile_aliases = {
        profile.id: _aliases(profile, figure_index.get(normalize_public_name(profile.full_name)))
        for profile in profiles
    }
    counters = _Counters()
    collector = PublisherFeedCollector()
    now = datetime.now(UTC)

    for source in sources:
        try:
            items = await collector.collect(
                source.base_url,
                max_items=settings.free_rss_max_items_per_feed,
                timeout_seconds=settings.free_rss_request_timeout_seconds,
            )
        except (CollectionPolicyError, httpx.HTTPError) as exc:
            counters.errors.append(f"{source.name}: {type(exc).__name__}")
            continue
        counters.feeds_checked += 1
        counters.entries_seen += len(items)
        for item in items:
            matched_profiles = [
                profile for profile in profiles if _matches(item, profile_aliases[profile.id])
            ]
            if not matched_profiles:
                counters.unmatched += 1
                continue
            source_row = await _source_record(db, source, item)
            for profile in matched_profiles:
                appearance = classify_publisher_appearance(item, profile_aliases[profile.id])
                duplicate = (
                    await db.execute(
                        select(SignalEvent).where(
                            SignalEvent.subject_id == profile.id,
                            or_(
                                SignalEvent.content_hash == item.content_hash,
                                SignalEvent.url == item.url,
                            ),
                        )
                    )
                ).scalar_one_or_none()
                if duplicate:
                    if appearance and duplicate.event_type == "media_mention":
                        duplicate.event_type = "public_appearance"
                        duplicate.provenance = {
                            **(duplicate.provenance or {}),
                            "classification_confidence": appearance.confidence,
                            "classification_basis": appearance.basis,
                            "appearance_kind": appearance.kind,
                            "appearance_description": appearance.description,
                            "is_inference": True,
                        }
                        counters.appearances_created += 1
                    counters.duplicates += 1
                    continue
                signal = SignalEvent(
                    subject_id=profile.id,
                    collection_source_id=source.id,
                    source_id=source_row.id,
                    external_id=item.external_id,
                    platform=urlparse(item.url).hostname or source.name,
                    event_type="public_appearance" if appearance else "media_mention",
                    language=str((source.source_metadata or {}).get("language") or "und"),
                    title=item.title,
                    content=item.summary or item.title,
                    url=item.url,
                    published_at=item.published_at,
                    observed_at=now,
                    engagement={},
                    geography={"scope": "Philippines", "basis": "publisher_catalog"},
                    provenance={
                        "authority": "publisher_rss",
                        "connector": "rss",
                        "captured_at": now.isoformat(),
                        "source_rights": "headline_excerpt_link_only",
                        "metric_denominator": {"feed_entries_seen": len(items)},
                        "classification_confidence": 1.0,
                        "observation_type": "observed",
                        "match_rule": "exact_profile_name_or_alias",
                        "is_inference": False,
                        **(
                            {
                                "classification_confidence": appearance.confidence,
                                "classification_basis": appearance.basis,
                                "appearance_kind": appearance.kind,
                                "appearance_description": appearance.description,
                                "is_inference": True,
                            }
                            if appearance
                            else {}
                        ),
                    },
                    content_hash=item.content_hash,
                    is_public=True,
                )
                db.add(signal)
                counters.signals_created += 1
                counters.appearances_created += int(appearance is not None)
        source.last_collected_at = now
        await db.flush()

    if settings.free_youtube_feeds_enabled:
        youtube = await collect_official_youtube_appearances(
            db,
            max_items_per_feed=settings.free_youtube_max_items_per_feed,
            timeout_seconds=settings.free_rss_request_timeout_seconds,
        )
        counters.feeds_checked += youtube.feeds_checked
        counters.entries_seen += youtube.entries_seen
        counters.signals_created += youtube.signals_created
        counters.duplicates += youtube.duplicates
        counters.unmatched += youtube.unmatched
        counters.appearances_created += youtube.appearances_created
        counters.errors.extend(youtube.errors)

    counters.opinions_created = await _create_assessments(db, profiles, profile_aliases)
    await db.commit()
    return FreeFeedCollectionOut(**vars(counters))
