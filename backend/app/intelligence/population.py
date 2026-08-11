"""Validated boundary for aggregate population-response estimators.

Providers receive only bounded evidence projections. They must not infer an
individual's beliefs or turn neural-response outputs into electoral claims.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Protocol

_POSITIVE = {
    "support",
    "supported",
    "trust",
    "credible",
    "progress",
    "effective",
    "approve",
    "suporta",
    "tiwala",
    "mahusay",
    "pag-unlad",
    "tagumpay",
    "sang-ayon",
}
_NEGATIVE = {
    "oppose",
    "opposed",
    "distrust",
    "corrupt",
    "failure",
    "reject",
    "crisis",
    "tutol",
    "katiwalian",
    "kabiguan",
    "ayaw",
    "krisis",
    "hindi",
}


@dataclass(frozen=True)
class EvidenceObservation:
    content: str
    authority: str | None


@dataclass(frozen=True)
class PopulationEstimate:
    forecast: dict[str, Any]
    assumptions: list[str]
    model_version: str


class PopulationResponseProvider(Protocol):
    model_version: str

    def estimate(
        self,
        observations: Sequence[EvidenceObservation],
        *,
        evaluated_at: datetime,
    ) -> PopulationEstimate: ...


class ConservativeLexicalBaseline:
    """Low-confidence baseline used until a validated provider is licensed."""

    model_version = "scenario-baseline-v1"

    @staticmethod
    def _sentiment_score(text: str) -> float:
        words = {part.strip(".,!?;:()[]{}\"'").lower() for part in text.split()}
        positives = len(words & _POSITIVE)
        negatives = len(words & _NEGATIVE)
        return (positives - negatives) / max(positives + negatives, 1)

    def estimate(
        self,
        observations: Sequence[EvidenceObservation],
        *,
        evaluated_at: datetime,
    ) -> PopulationEstimate:
        representative = any(
            item.authority in {"representative_poll", "consented_panel"} for item in observations
        )
        scores = [self._sentiment_score(item.content) for item in observations]
        lexical = sum(scores) / len(scores) if scores else 0.0
        enough = len(observations) >= 5
        confidence_cap = 0.82 if representative else 0.58
        confidence = (
            min(confidence_cap, 0.18 + math.log1p(len(observations)) / 10) if enough else 0.1
        )
        central = round(lexical * 8, 1) if enough else 0.0
        uncertainty = max(4.0, 14.0 - min(len(observations), 100) / 10)
        if not enough:
            direction = "insufficient_evidence"
        elif abs(central) < 1.5:
            direction = "mixed"
        else:
            direction = "positive" if central > 0 else "negative"
        return PopulationEstimate(
            forecast={
                "direction": direction,
                "lower_pct": round(central - uncertainty, 1),
                "central_pct": central,
                "upper_pct": round(central + uncertainty, 1),
                "confidence": round(confidence, 3),
                "signal_count": len(observations),
                "representative_calibration": representative,
                "valid_until": (evaluated_at + timedelta(hours=24)).isoformat(),
                "classification": "estimate",
            },
            assumptions=[
                "Only evidence available at or before effective_at was used.",
                "Public online activity is not a representative sample of the electorate.",
                "The cohort is aggregate and contains at least 100 observations.",
                "Causal impact is not established by observational sentiment.",
            ],
            model_version=self.model_version,
        )


population_response_provider: PopulationResponseProvider = ConservativeLexicalBaseline()
