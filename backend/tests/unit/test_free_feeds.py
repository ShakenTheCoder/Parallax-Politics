from __future__ import annotations

from datetime import UTC, datetime

from app.intelligence.free_feeds import (
    DEFAULT_FREE_FEEDS,
    _assessment_summary,
    _importance,
    _matches,
)
from app.intelligence.rss import FeedItem, PublisherFeedCollector
from app.models.intelligence import SignalEvent
from app.schemas.intelligence import CollectionSourceCreate


async def test_publisher_feed_collector_normalizes_rss(monkeypatch) -> None:
    body = b"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0"><channel><title>Publisher</title><item>
      <guid>story-1</guid><title>Sara Duterte gives an interview</title>
      <link>https://publisher.example/story-1</link>
      <description><![CDATA[<b>Interview</b> on public policy.]]></description>
      <pubDate>Mon, 24 Aug 2026 08:00:00 +0000</pubDate>
    </item></channel></rss>"""

    class Response:
        content = body
        is_redirect = False

        def raise_for_status(self) -> None:
            return None

    class Client:
        def __init__(self, **_kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args) -> None:
            return None

        async def get(self, _url: str) -> Response:
            return Response()

    async def allowed(_url: str) -> None:
        return None

    monkeypatch.setattr("app.intelligence.rss.httpx.AsyncClient", Client)
    monkeypatch.setattr("app.intelligence.rss.validate_public_destination", allowed)
    items = await PublisherFeedCollector().collect(
        "https://publisher.example/feed.xml", max_items=10, timeout_seconds=5
    )

    assert len(items) == 1
    assert items[0].title == "Sara Duterte gives an interview"
    assert items[0].summary == "Interview on public policy."
    assert items[0].published_at == datetime(2026, 8, 24, 8, tzinfo=UTC)


def test_profile_matching_uses_bounded_exact_aliases() -> None:
    item = FeedItem(
        external_id="1",
        title="Sara Duterte addresses regional officials",
        summary="",
        url="https://example.com/story",
        published_at=None,
        content_hash="hash",
    )
    assert _matches(item, ("sara duterte",)) is True
    assert _matches(item, ("ara dut",)) is False


def test_assessment_is_descriptive_and_importance_is_word_based() -> None:
    signals = [
        SignalEvent(
            subject_id=None,
            platform="publisher.example",
            event_type="media_mention",
            language="en",
            title="Public service program discussed",
            content="Excerpt",
            url="https://publisher.example/story",
            observed_at=datetime.now(UTC),
            engagement={},
            geography={},
            provenance={},
            content_hash="hash",
            is_public=True,
        )
    ]
    summary = _assessment_summary(signals)
    assert "media attention, not public opinion" in summary
    assert _importance(1, 1) == "low"
    assert _importance(5, 3) == "high"
    assert _importance(8, 4) == "critical"


def test_assessment_leads_with_headlines_that_name_the_subject() -> None:
    signals = [
        SignalEvent(
            subject_id=None,
            platform="publisher.example",
            event_type="media_mention",
            language="en",
            title=title,
            content="Sara Duterte is discussed.",
            url=f"https://publisher.example/{index}",
            observed_at=datetime.now(UTC),
            engagement={},
            geography={},
            provenance={},
            content_hash=str(index),
            is_public=True,
        )
        for index, title in enumerate(
            [
                "A senator questions a witness",
                "Sara Duterte trial enters another day",
            ]
        )
    ]

    summary = _assessment_summary(signals, ("sara duterte",))

    assert summary.index("Sara Duterte trial") < summary.index("A senator questions")


def test_curated_free_feeds_are_https_and_rss_connector_is_valid() -> None:
    assert len(DEFAULT_FREE_FEEDS) >= 4
    assert all(feed.url.startswith("https://") for feed in DEFAULT_FREE_FEEDS)
    payload = CollectionSourceCreate.model_validate(
        {
            "name": "Publisher RSS",
            "base_url": "https://publisher.example/feed.xml",
            "authority": "public_web",
            "connector_kind": "rss",
        }
    )
    assert payload.connector_kind == "rss"
