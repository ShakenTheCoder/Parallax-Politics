from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.poll import PollCreate
from app.services.audience_experiments import _aggregate, _validate_sample


def test_poll_requires_ordered_field_and_publication_dates() -> None:
    with pytest.raises(ValidationError):
        PollCreate(
            pollster="Example Pollster",
            published_at=date(2026, 1, 1),
            field_start=date(2026, 2, 1),
            field_end=date(2026, 2, 2),
            sample_size=1000,
            population="Adults",
            mode="Face to face",
            margin_of_error="±3%",
            exact_question="A sufficiently detailed exact question?",
            geography="Philippines",
            source_url="https://example.com/poll.pdf",
        )


def test_audience_sample_requires_every_variant_and_cohort() -> None:
    variants = [{"id": "a", "title": "A", "message": "A sufficiently long message for testing."}]
    cohorts = [{"id": "c", "label": "C"}]
    with pytest.raises(ValueError, match="every configured"):
        _validate_sample({"evaluations": []}, variants, cohorts)


def test_audience_aggregate_exposes_consensus_and_variance_only() -> None:
    variants = [{"id": "a", "title": "A", "message": "A sufficiently long message for testing."}]
    samples = [{"evaluations": [{"variant_id": "a", "cohort_id": "c", "criteria": dict.fromkeys(("clarity", "relevance", "credibility", "objection_risk", "recall", "sharing_inclination"), 3), "note": ""}]} for _ in range(3)]
    aggregate = _aggregate(samples, variants)
    assert aggregate["samples"] == 3
    assert aggregate["variants"]["a"]["clarity"] == {"consensus": 3.0, "variance": 0.0, "observations": 3}
    assert "best_segment" not in aggregate
