from datetime import UTC, datetime

from app.intelligence.population import (
    ConservativeLexicalBaseline,
    EvidenceObservation,
)


def test_baseline_abstains_when_evidence_is_sparse() -> None:
    estimate = ConservativeLexicalBaseline().estimate(
        [EvidenceObservation(content="support progress", authority="public_web")],
        evaluated_at=datetime(2026, 8, 11, tzinfo=UTC),
    )
    assert estimate.forecast["direction"] == "insufficient_evidence"
    assert estimate.forecast["confidence"] == 0.1


def test_public_web_estimate_remains_below_uncalibrated_cap() -> None:
    estimate = ConservativeLexicalBaseline().estimate(
        [EvidenceObservation(content="support progress", authority="public_web")] * 500,
        evaluated_at=datetime(2026, 8, 11, tzinfo=UTC),
    )
    assert estimate.forecast["confidence"] <= 0.58
    assert estimate.forecast["representative_calibration"] is False


def test_representative_source_is_recorded_as_calibration() -> None:
    observations = [
        EvidenceObservation(content="mixed public response", authority="public_web")
    ] * 9
    observations.append(
        EvidenceObservation(content="representative estimate", authority="representative_poll")
    )
    estimate = ConservativeLexicalBaseline().estimate(
        observations,
        evaluated_at=datetime(2026, 8, 11, tzinfo=UTC),
    )
    assert estimate.forecast["representative_calibration"] is True
