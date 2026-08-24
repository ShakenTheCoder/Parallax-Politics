from __future__ import annotations

from datetime import UTC, datetime

from app.intelligence.appearance_classifier import (
    classify_owned_youtube_appearance,
    classify_publisher_appearance,
)
from app.intelligence.brief_view import _caption
from app.intelligence.official_youtube import _youtube_channels
from app.intelligence.rss import FeedItem
from app.models.intelligence import SignalEvent
from app.models.political_figure import PoliticalFigure


def _item(title: str, summary: str = "") -> FeedItem:
    return FeedItem(
        external_id="video-1",
        title=title,
        summary=summary,
        url="https://www.youtube.com/watch?v=video-1",
        published_at=datetime(2026, 8, 24, 9, tzinfo=UTC),
        content_hash="hash",
    )


def test_publisher_classifier_requires_a_direct_appearance_cue() -> None:
    interview = classify_publisher_appearance(
        _item(
            "Sara Duterte gives media interview",
            "The vice president answered questions after the public event.",
        ),
        ("sara duterte",),
    )
    trial_blog = classify_publisher_appearance(
        _item("LIVE Coverage: Sara Duterte impeachment trial"),
        ("sara duterte",),
    )

    assert interview is not None
    assert interview.kind == "interview"
    assert trial_blog is None


def test_owned_youtube_message_produces_a_short_evidence_derived_description() -> None:
    decision = classify_owned_youtube_appearance(
        _item(
            "AUGUST 24, 2026 | PAALALA SA PAG-ULAN AT BAGYO",
            "Mga Kababayan. Magandang araw sa inyong lahat. "
            "Ang pinakamabisang panlaban sa anumang kalamidad ay ang ating kahandaan.",
        ),
        "Sara Duterte",
    )

    assert decision is not None
    assert decision.kind == "speech"
    assert "ating kahandaan" in decision.description
    assert len(decision.description) <= 260


def test_only_channel_id_youtube_accounts_become_collectable_feeds() -> None:
    figure = PoliticalFigure(
        canonical_name="Raffy Tulfo",
        aliases=[],
        social_accounts=[
            {
                "platform": "YouTube",
                "url": "https://www.youtube.com/channel/UCxhygwqQ1ZMoBGQM2yEcNug",
            },
            {
                "platform": "YouTube",
                "url": "https://www.youtube.com/channel/raffytulfoinaction",
            },
        ],
    )

    assert _youtube_channels(figure) == [
        (
            "UCxhygwqQ1ZMoBGQM2yEcNug",
            "https://www.youtube.com/channel/UCxhygwqQ1ZMoBGQM2yEcNug",
        )
    ]


def test_brief_uses_the_evidence_derived_appearance_description() -> None:
    signal = SignalEvent(
        subject_id=None,
        platform="YouTube · Sara Duterte",
        event_type="public_appearance",
        language="fil",
        title="Weather message",
        content="Long source description",
        url="https://www.youtube.com/watch?v=video-1",
        observed_at=datetime.now(UTC),
        engagement={},
        geography={},
        provenance={"appearance_description": "A short source-backed description."},
        content_hash="hash",
        is_public=True,
    )

    assert _caption(signal) == "A short source-backed description."
