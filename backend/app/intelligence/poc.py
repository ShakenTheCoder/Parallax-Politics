"""Curated, provenance-bearing fallback snapshot for the August 2026 POC.

The fixture is intentionally explicit about low connector coverage.  It keeps
the app useful during a provider outage without presenting demo-normalized
components as live observations or publishing a competitive rank.
"""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

from app.intelligence.momentum import (
    COMPONENT_WEIGHTS,
    MOMENTUM_VERSION,
    RANK_COVERAGE_THRESHOLD,
    campaign_momentum_score,
    publishable_rank,
    seven_day_delta,
)

EFFECTIVE_AT = datetime(2026, 8, 24, 9, 0, tzinfo=UTC)
PULSE_ASIA_URL = (
    "https://pulseasia.ph/wp-content/uploads/2026/07/"
    "MR2-UB2026-2-MR-on-the-May-2028-Elections-Final.pdf"
)

WATCHLIST: list[dict[str, Any]] = [
    {"slug": "sara-duterte", "name": "Sara Duterte", "office": "Vice-President of the Philippines", "poll": 49.0, "strongest_channel": "Public video", "issue": "Executive leadership"},
    {"slug": "leni-robredo", "name": "Leni Robredo", "office": "Mayor of Naga City", "poll": 26.0, "strongest_channel": "Earned media", "issue": "Good governance"},
    {"slug": "raffy-tulfo", "name": "Raffy Tulfo", "office": "Senator of the Philippines", "poll": 14.0, "strongest_channel": "YouTube", "issue": "Public service"},
    {"slug": "vince-dizon", "name": "Vince Dizon", "office": "DPWH Secretary at poll publication", "poll": 1.0, "strongest_channel": "News", "issue": "Infrastructure delivery"},
    {"slug": "benjamin-magalong", "name": "Benjamin Magalong", "office": "Baguio City Mayor at poll publication", "poll": 1.0, "strongest_channel": "Local news", "issue": "Local governance"},
    {"slug": "nicolas-torre-iii", "name": "Nicolas Torre III", "office": "MMDA General Manager at poll publication", "poll": 0.1, "strongest_channel": "News", "issue": "Metropolitan operations"},
]

EVIDENCE: list[dict[str, Any]] = [
    {
        "id": "ev-pulse-jul-2026",
        "title": "Pulse Asia July 2026 nationwide survey on the May 2028 elections",
        "url": PULSE_ASIA_URL,
        "source": "Pulse Asia Research, Inc.",
        "published_at": "2026-07-22",
        "captured_at": EFFECTIVE_AT.isoformat(),
        "layer": "polling",
        "rights": "link_and_derived_facts",
        "geography": "Philippines",
        "classification_confidence": 1.0,
        "observation_type": "observed",
    },
    {
        "id": "ev-constitution",
        "title": "1987 Constitution of the Philippines",
        "url": "https://lawphil.net/consti/cons1987.html",
        "source": "LawPhil",
        "published_at": "1987-02-11",
        "captured_at": EFFECTIVE_AT.isoformat(),
        "layer": "official_record",
        "rights": "public_legal_record",
        "geography": "Philippines",
        "classification_confidence": 1.0,
        "observation_type": "observed",
    },
    {
        "id": "ev-naga-mayor",
        "title": "City Mayor's Office — Maria Leonor G. Robredo",
        "url": "https://www2.naga.gov.ph/office-service/city-mayors-office/",
        "source": "City Government of Naga",
        "published_at": None,
        "captured_at": EFFECTIVE_AT.isoformat(),
        "layer": "official_record",
        "rights": "public_web_attribution",
        "geography": "Naga City",
        "classification_confidence": 1.0,
        "observation_type": "observed",
    },
    {
        "id": "ev-tulfo-senate",
        "title": "Senator Raffy Tulfo biography",
        "url": "https://legacy.senate.gov.ph/senators/sen_bio/tulfo_raffy_bio.asp",
        "source": "Senate of the Philippines",
        "published_at": None,
        "captured_at": EFFECTIVE_AT.isoformat(),
        "layer": "official_record",
        "rights": "public_web_attribution",
        "geography": "Philippines",
        "classification_confidence": 1.0,
        "observation_type": "observed",
    },
]


def _timeline() -> list[dict[str, Any]]:
    dates = [f"2026-08-{day:02d}" for day in range(11, 25)]
    bases = [62, 58, 57, 48, 46, 42]
    return [
        {
            "date": date,
            "values": {
                figure["slug"]: round(base + ((index * (position + 2)) % 7 - 2) * 0.7, 1)
                for position, (figure, base) in enumerate(zip(WATCHLIST, bases, strict=True))
            },
        }
        for index, date in enumerate(dates)
    ]


def _archetypes() -> list[dict[str, Any]]:
    definitions = [
        ("Metro young voters", "NCR · 18–30 · urban · Filipino/English"),
        ("Luzon working commuters", "Balance Luzon · 31–59 · urban/peri-urban"),
        ("Luzon rural households", "Balance Luzon · adult · rural"),
        ("Visayas connected youth", "Visayas · 18–30 · Filipino/Cebuano"),
        ("Visayas working families", "Visayas · 31–59 · mixed urbanicity"),
        ("Mindanao connected youth", "Mindanao · 18–30 · Filipino/Cebuano"),
        ("Mindanao working communities", "Mindanao · 31–59 · mixed urbanicity"),
        ("Older news followers", "Philippines · 60+ · mixed urbanicity"),
    ]
    scores = [4.0, 3.7, 3.4, 3.8, 3.6, 3.5, 3.5, 3.9]
    return [
        {
            "name": name,
            "basis": basis,
            "synthetic": True,
            "sample_runs": 3,
            "consensus": score,
            "variance": round(0.12 + (index % 3) * 0.05, 2),
            "rubric": {
                "clarity": score,
                "relevance": round(score - 0.2, 1),
                "credibility": round(score - 0.3, 1),
                "objection_risk": round(5.0 - score + 0.5, 1),
                "recall": round(score - 0.1, 1),
                "sharing_inclination": round(score - 0.5, 1),
            },
            "note": "Qualitative synthetic rubric; not polling or voter intent.",
        }
        for index, ((name, basis), score) in enumerate(zip(definitions, scores, strict=True))
    ]


def command_view() -> dict[str, Any]:
    components = {
        "public_attention": 72.0,
        "channel_normalized_resonance": 66.0,
        "net_favorability": 61.0,
        "earned_media_visibility": 69.0,
        "search_interest": 67.0,
        "issue_ownership": 63.0,
    }
    score = campaign_momentum_score(components)
    previous = 62.4
    coverage = 0.54
    return {
        "subject": "Sara Duterte",
        "watch_status": "polled_hypothetical",
        "score": score,
        "previous_score": previous,
        "delta": seven_day_delta(score, previous),
        "rank": publishable_rank(1, coverage),
        "rank_suppressed": True,
        "coverage_confidence": coverage,
        "freshness_minutes": None,
        "model_version": MOMENTUM_VERSION,
        "headline": "Public-video attention is the largest modeled contributor, but rank is withheld because competitor-wide social and search feeds are incomplete.",
        "tiles": [
            {"key": "attention", "label": "Attention share", "value": "31.8%", "delta": "+3.6 pts", "evidence_ids": []},
            {"key": "favorability", "label": "Net favorability", "value": "+18", "delta": "+2.1 pts", "evidence_ids": []},
            {"key": "earned", "label": "Earned visibility", "value": "69 / 100", "delta": "+4.4", "evidence_ids": []},
            {"key": "search", "label": "Search interest", "value": "67 / 100", "delta": "+5.2", "evidence_ids": []},
            {"key": "appearance", "label": "Strongest message", "value": "Service delivery", "delta": "24h lift +8%", "evidence_ids": []},
        ],
        "opportunity": "Convert attention into one specific, source-backed service-delivery message and measure equal-age response.",
        "risk": "The apparent movement may be platform-skewed while Meta and TikTok competitor coverage remains incomplete.",
        "next_move": "Analyst-reviewed demo action: commission a source-complete 72-hour comparison before any campaign decision.",
        "next_move_reviewed": True,
        "coverage_note": "Provisional POC normalization. No competitive rank is publishable below 60% coverage.",
    }


def analysis_center() -> dict[str, Any]:
    command = command_view()
    return {
        "snapshot": {
            "kind": "analysis_center",
            "effective_at": EFFECTIVE_AT.isoformat(),
            "produced_by": "curated-poc-fixture",
            "model_version": MOMENTUM_VERSION,
            "mode": "frozen_fallback",
            "notice": "A labeled frozen POC snapshot is shown. Live social/search connectors are not configured.",
        },
        "election": {
            "label": "Expected regular presidential election",
            "date": "2028-05-08",
            "official_calendar_status": "pending",
            "watchlist_label": "Research watchlist — not filed candidates",
        },
        "command_view": command,
        "momentum_components": [
            {"key": key, "label": key.replace("_", " ").title(), "weight": weight, "score": value, "delta": round((value - 60) / 5, 1)}
            for (key, weight), value in zip(COMPONENT_WEIGHTS.items(), [72, 66, 61, 69, 67, 63], strict=True)
        ],
        "timeline": _timeline(),
        "watchlist": [
            {
                **figure,
                "watch_status": "polled_hypothetical",
                "rank": None,
                "momentum": round(66.8 - index * 4.7, 1),
                "movement": round(4.4 - index * 1.2, 1),
                "earned_visibility": max(39, 70 - index * 6),
                "cadence": ["High", "Medium", "High", "Low", "Medium", "Low"][index],
            }
            for index, figure in enumerate(WATCHLIST)
        ],
        "channels": [
            {"name": "News / RSS", "score": 69, "coverage": 0.78, "comparison": "Eligible public reporting; clustered by story"},
            {"name": "YouTube", "score": 66, "coverage": 0.61, "comparison": "Equal-age public video snapshots"},
            {"name": "X", "score": None, "coverage": 0.0, "comparison": "Credential and $50 cap required"},
            {"name": "Facebook / Instagram", "score": None, "coverage": 0.22, "comparison": "Owned authorization absent; competitor-wide access incomplete"},
            {"name": "TikTok", "score": None, "coverage": 0.0, "comparison": "Licensed or authorized access required"},
        ],
        "narratives": [
            {"name": "Service delivery", "stage": "accelerating", "velocity": 18.0, "owner": "mixed", "source_diversity": 3.2, "evidence_ids": []},
            {"name": "Good governance", "stage": "persistent", "velocity": 7.0, "owner": "Leni Robredo", "source_diversity": 2.7, "evidence_ids": ["ev-naga-mayor"]},
            {"name": "Public assistance", "stage": "persistent", "velocity": 9.0, "owner": "Raffy Tulfo", "source_diversity": 2.4, "evidence_ids": ["ev-tulfo-senate"]},
        ],
        "appearances": [
            {
                "id": "appearance-demo-1",
                "title": "Service-delivery public remarks",
                "figure": "Sara Duterte",
                "occurred_at": "2026-08-20T02:00:00+00:00",
                "source_status": "transcript_pending",
                "topics": [{"label": "Service delivery", "share": 0.46}, {"label": "National leadership", "share": 0.32}, {"label": "Other", "share": 0.22}],
                "message_consistency": 0.74,
                "quote_pickup": 4,
                "lift": {"6h": 3.0, "24h": 8.0, "72h": 5.0},
                "evidence_ids": [],
            }
        ],
        "audience_lab": _archetypes(),
        "latest_poll": {
            "pollster": "Pulse Asia Research, Inc.",
            "published_at": "2026-07-22",
            "field_dates": "June 28–July 3 and July 6, 2026",
            "sample": 2400,
            "population": "Representative adults aged 18+",
            "mode": "Face-to-face interviews",
            "margin_of_error": "±2 percentage points nationally at 95% confidence",
            "question": "Who would you vote for as President if the May 2028 election were held during the survey period and the listed people were candidates?",
            "source_url": PULSE_ASIA_URL,
            "layer": "polling",
            "results": [{"name": figure["name"], "value": figure["poll"]} for figure in WATCHLIST],
        },
        "coverage": {
            "confidence": command["coverage_confidence"],
            "threshold": RANK_COVERAGE_THRESHOLD,
            "rank_suppressed": True,
            "families": [
                {"name": "News / RSS", "status": "partial", "score": 0.78, "freshness": "frozen Aug 24", "action": "Enable scheduled feeds"},
                {"name": "Public video", "status": "partial", "score": 0.61, "freshness": "frozen Aug 24", "action": "Configure YouTube key"},
                {"name": "Search", "status": "missing", "score": 0.0, "freshness": None, "action": "Import timestamped Trends comparison"},
                {"name": "Polling", "status": "current", "score": 1.0, "freshness": "published Jul 22", "action": "Monitor new comparable releases"},
                {"name": "Official records", "status": "partial", "score": 0.72, "freshness": "checked Aug 24", "action": "Finish four profile verifications"},
                {"name": "Appearances", "status": "partial", "score": 0.35, "freshness": "transcript pending", "action": "Load approved recordings/transcripts"},
            ],
            "missing_sources": ["X", "Google Trends", "TikTok", "authorized Meta analytics", "four official profile refreshes"],
        },
        "evidence": EVIDENCE,
        "provider_status": {
            "live_connectors": "unavailable",
            "fallback": "frozen_snapshot_loaded",
            "scenario_provider": "requires NVIDIA_API_KEY",
        },
    }


def compare_variants(variants: list[dict[str, str]]) -> dict[str, Any]:
    criteria = ["clarity", "relevance", "credibility", "objection_risk", "recall", "sharing_inclination"]
    results: list[dict[str, Any]] = []
    for variant in variants:
        digest = sha256((variant["title"] + variant["message"]).encode()).digest()
        rubric = {
            criterion: round(2.5 + (digest[index] / 255) * 2.0, 1)
            for index, criterion in enumerate(criteria)
        }
        results.append(
            {
                "id": variant["id"],
                "title": variant["title"],
                "rubric": rubric,
                "consensus": round(sum(rubric.values()) / len(rubric), 1),
                "variance": round(0.1 + digest[7] / 255 * 0.3, 2),
                "sample_runs_per_cohort": 3,
                "label": "synthetic qualitative fallback — not polling or voter intent",
            }
        )
    return {
        "context_pack": "philippines-2028-poc-2026-08-24",
        "provider_status": "frozen_deterministic_fallback",
        "cohorts": 8,
        "results": results,
        "warnings": [
            "No vote-share or individual-response claim is produced.",
            "A live model run requires a configured provider and must retain all three samples per cohort.",
        ],
    }

