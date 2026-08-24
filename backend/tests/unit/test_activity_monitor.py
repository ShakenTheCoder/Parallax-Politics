from __future__ import annotations

from datetime import UTC, datetime

from app.intelligence.activity_monitor import (
    ActivityExtraction,
    activity_change,
    enforce_publisher_evidence_layer,
    monitoring_state,
    normalize_extraction,
)
from app.intelligence.activity_sources import _account_source
from app.intelligence.rss import FeedItem
from app.models.political_activity import PoliticalActivitySource
from app.models.political_figure import PoliticalFigure


def _figure() -> PoliticalFigure:
    return PoliticalFigure(
        slug="example-person",
        canonical_name="Example Person",
        aliases=["Example P."],
        category="watchlist",
        current_role="Public official",
        office="Public office",
        jurisdiction="Philippines",
        status="active",
        data={},
        social_accounts=[],
        relationships=[],
        source_ledger=[],
        coverage_gaps=[],
        confidence=0.8,
    )


def test_monitoring_state_compares_equal_windows() -> None:
    assert monitoring_state(0, 0) == "quiet"
    assert monitoring_state(1, 0) == "active"
    assert monitoring_state(2, 0) == "emerging"
    assert monitoring_state(4, 2) == "emerging"
    assert monitoring_state(3, 2) == "active"
    assert activity_change(2, 1) == "up"
    assert activity_change(1, 2) == "down"
    assert activity_change(2, 2) == "steady"


def test_layer_and_type_cannot_contradict_each_other() -> None:
    extraction = ActivityExtraction(
        relevant=True,
        evidence_layer="public_statement",
        appearance_type="indirect_coverage",
        topic="Medical leave",
        summary="The public source attributes a written announcement to the person.",
        confidence=0.8,
    )
    assert normalize_extraction(extraction).appearance_type == "written_statement"


def test_publisher_mention_cannot_be_promoted_without_headline_evidence() -> None:
    source = PoliticalActivitySource(
        name="Publisher",
        url="https://publisher.example/feed",
        source_class="publisher",
        platform="news",
        access_method="rss",
        publisher="Publisher",
        status="active",
        schedule_minutes=15,
        rights="headline_excerpt_and_link",
        reliability_tier="secondary",
        robots_observed=True,
        source_metadata={},
    )
    item = FeedItem(
        external_id="1",
        title="Highlights from the Example Person proceedings",
        summary="Example Person was discussed by other participants.",
        url="https://publisher.example/story",
        published_at=datetime.now(UTC),
        content_hash="a" * 64,
    )
    extraction = ActivityExtraction(
        relevant=True,
        evidence_layer="public_statement",
        appearance_type="speech_or_statement",
        topic="Proceedings",
        summary="The article summarizes what others said about the person.",
        confidence=0.9,
    )
    guarded = enforce_publisher_evidence_layer(source, _figure(), item, extraction)
    assert guarded.evidence_layer == "indirect_coverage"
    assert guarded.appearance_type == "indirect_coverage"


def test_social_platforms_are_registered_but_not_scraped() -> None:
    source = _account_source(
        _figure(),
        {
            "platform": "Facebook",
            "url": "https://www.facebook.com/example",
            "verification": "listed_by_official_source",
        },
    )
    assert source is not None
    assert source["access_method"] == "official_api"
    assert source["status"] == "authorization_required"


def test_youtube_requires_reviewed_immutable_channel_id() -> None:
    valid = _account_source(
        _figure(),
        {
            "platform": "YouTube",
            "url": "https://www.youtube.com/channel/UCqgTKnYIeu4DNXGN5fBCY9Q",
            "verification": "claimed_on_wikidata",
        },
    )
    assert valid is not None
    assert valid["access_method"] == "youtube_atom"
    assert valid["status"] == "needs_review"

    handle = _account_source(
        _figure(),
        {"platform": "YouTube", "url": "https://www.youtube.com/@example"},
    )
    assert handle is not None
    assert handle["status"] == "needs_channel_id"


def test_public_website_stays_review_only_until_connector_check() -> None:
    source = _account_source(
        _figure(),
        {
            "platform": "Website",
            "url": "https://example.gov.ph/news",
            "verification": "listed_by_official_source",
        },
    )
    assert source is not None
    assert source["access_method"] == "scrapling"
    assert source["status"] == "needs_review"
