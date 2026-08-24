from __future__ import annotations

from app.intelligence.momentum import (
    CoverageInput,
    MetricObservation,
    campaign_momentum_score,
    component_scores,
    coverage_confidence,
    deduplicate_signals,
    publishable_rank,
    seven_day_delta,
)


def test_campaign_momentum_uses_versioned_weights() -> None:
    score = campaign_momentum_score(
        {
            "public_attention": 72,
            "channel_normalized_resonance": 66,
            "net_favorability": 61,
            "earned_media_visibility": 69,
            "search_interest": 67,
            "issue_ownership": 63,
        }
    )
    assert score == 66.8


def test_campaign_momentum_does_not_silently_reweight_missing_components() -> None:
    assert campaign_momentum_score({"public_attention": 80}) is None


def test_normalization_is_platform_and_format_native() -> None:
    scores = component_scores(
        [
            MetricObservation("public_attention", "youtube", "short", 10, "observed"),
            MetricObservation("public_attention", "youtube", "short", 30, "observed"),
            MetricObservation("public_attention", "news", "article", 900, "observed"),
            MetricObservation("public_attention", "news", "article", 900, "owned"),
        ]
    )
    # YouTube contributes 0 and 100; the tied news group contributes 50 and 50.
    assert scores["public_attention"] == 50.0


def test_polling_and_synthetic_layers_are_excluded_before_normalization() -> None:
    scores = component_scores(
        [
            MetricObservation("search_interest", "trends", "query", 20, "observed"),
            MetricObservation("search_interest", "trends", "query", 40, "observed"),
            MetricObservation("search_interest", "trends", "query", 10000, "polling"),
            MetricObservation("search_interest", "trends", "query", 20000, "synthetic"),
        ]
    )
    assert scores["search_interest"] == 50.0


def test_seven_day_delta_and_coverage_gate() -> None:
    assert seven_day_delta(66.8, 62.4) == 4.4
    assert publishable_rank(1, 0.599) is None
    assert publishable_rank(1, 0.60) == 1


def test_coverage_is_weighted_across_quality_dimensions() -> None:
    confidence = coverage_confidence(
        [
            CoverageInput("news", 0.75, 1, 1, 1, 1),
            CoverageInput("social", 0.25, 0, 0, 0, 0),
        ]
    )
    assert confidence == 0.75


def test_deduplication_uses_subject_and_canonical_identity() -> None:
    rows = [
        {"subject_id": "a", "url": "https://news.example/story?utm_source=x"},
        {"subject_id": "a", "url": "https://news.example/story"},
        {"subject_id": "b", "url": "https://news.example/story"},
        {"subject_id": "a", "content_hash": "different", "url": "https://news.example/story"},
    ]
    result = deduplicate_signals(rows)
    assert len(result) == 3
    assert [row["subject_id"] for row in result] == ["a", "b", "a"]

