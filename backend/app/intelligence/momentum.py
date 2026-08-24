"""Deterministic Campaign Momentum policy.

This module is deliberately independent of SQLAlchemy and providers.  It owns
the inclusion, normalization, coverage and rank-gating invariants so every API
surface uses the same rules.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

EvidenceLayer = Literal["observed", "owned", "polling", "synthetic"]

MOMENTUM_VERSION = "cmi-2028-poc-v1"
COMPONENT_WEIGHTS: dict[str, float] = {
    "public_attention": 0.25,
    "channel_normalized_resonance": 0.20,
    "net_favorability": 0.20,
    "earned_media_visibility": 0.15,
    "search_interest": 0.10,
    "issue_ownership": 0.10,
}
INDEX_LAYERS: frozenset[str] = frozenset({"observed", "owned"})
RANK_COVERAGE_THRESHOLD = 0.60


@dataclass(frozen=True)
class MetricObservation:
    component: str
    platform: str
    content_format: str
    value: float
    layer: EvidenceLayer


@dataclass(frozen=True)
class CoverageInput:
    source_family: str
    weight: float
    availability: float
    freshness: float
    rights_usability: float
    denominator_quality: float


def _bounded(value: float) -> float:
    return min(1.0, max(0.0, value))


def normalize_within_platform(
    observations: list[MetricObservation],
) -> list[tuple[MetricObservation, float]]:
    """Min-max normalize only among like platform/format/component records.

    A tied group maps to 50 instead of creating a false winner.
    Polling and synthetic inputs are returned nowhere: exclusion happens before
    any statistic can affect the group bounds.
    """

    eligible = [item for item in observations if item.layer in INDEX_LAYERS]
    groups: dict[tuple[str, str, str], list[MetricObservation]] = defaultdict(list)
    for item in eligible:
        groups[(item.component, item.platform, item.content_format)].append(item)

    normalized: list[tuple[MetricObservation, float]] = []
    for items in groups.values():
        low = min(item.value for item in items)
        high = max(item.value for item in items)
        for item in items:
            score = 50.0 if high == low else (item.value - low) / (high - low) * 100
            normalized.append((item, round(score, 3)))
    return normalized


def component_scores(observations: list[MetricObservation]) -> dict[str, float | None]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for item, score in normalize_within_platform(observations):
        if item.component in COMPONENT_WEIGHTS:
            grouped[item.component].append(score)
    return {
        component: round(sum(grouped[component]) / len(grouped[component]), 1)
        if grouped[component]
        else None
        for component in COMPONENT_WEIGHTS
    }


def campaign_momentum_score(components: dict[str, float | None]) -> float | None:
    """Return the versioned score, or abstain when any component is missing."""

    if any(components.get(name) is None for name in COMPONENT_WEIGHTS):
        return None
    score = sum(float(components[name]) * weight for name, weight in COMPONENT_WEIGHTS.items())
    return round(score, 1)


def seven_day_delta(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None:
        return None
    return round(current - previous, 1)


def coverage_confidence(inputs: list[CoverageInput]) -> float:
    """Weighted mean of availability, freshness, rights and denominator quality."""

    total_weight = sum(max(item.weight, 0.0) for item in inputs)
    if total_weight <= 0:
        return 0.0
    score = 0.0
    for item in inputs:
        family_quality = (
            _bounded(item.availability)
            * _bounded(item.freshness)
            * _bounded(item.rights_usability)
            * _bounded(item.denominator_quality)
        ) ** 0.25
        score += max(item.weight, 0.0) * family_quality
    return round(score / total_weight, 3)


def publishable_rank(rank: int | None, coverage: float) -> int | None:
    return rank if coverage >= RANK_COVERAGE_THRESHOLD else None


def canonicalize_url(url: str) -> str:
    parts = urlsplit(url)
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in {"fbclid", "gclid"}
    ]
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), urlencode(query), "")
    )


def deduplicate_signals(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep the first observation for a subject/content identity.

    Content hash takes precedence; canonical URL is the bounded fallback.  The
    subject is part of the key so the same article may support multiple linked
    watchlist figures without violating storage uniqueness.
    """

    seen: set[tuple[str, str]] = set()
    result: list[dict[str, Any]] = []
    for record in records:
        subject = str(record.get("subject_id") or "unscoped")
        identity = str(record.get("content_hash") or "")
        if not identity:
            identity = canonicalize_url(str(record.get("url") or ""))
        key = (subject, identity)
        if key in seen:
            continue
        seen.add(key)
        result.append(record)
    return result
