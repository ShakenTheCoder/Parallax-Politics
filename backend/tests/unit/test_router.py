from app.llm.router import (
    HAIKU_4_5,
    OPUS_4_7,
    SONNET_4_7,
    ModelTier,
    estimate_cost_usd,
    pick_model,
)


def test_pick_model_tiers():
    assert pick_model(ModelTier.cheap) is HAIKU_4_5
    assert pick_model(ModelTier.default) is SONNET_4_7
    assert pick_model(ModelTier.escalate) is OPUS_4_7


def test_cost_estimate_known_rates():
    # Sonnet: $3/Mtok in, $15/Mtok out -> 1k in + 1k out = 0.003 + 0.015 = 0.018
    cost = estimate_cost_usd(SONNET_4_7, input_tokens=1_000, output_tokens=1_000)
    assert abs(cost - 0.018) < 1e-9


def test_cache_read_is_cheaper_than_input():
    # 1k cache-read tokens cost much less than 1k fresh input.
    fresh = estimate_cost_usd(SONNET_4_7, input_tokens=1000, output_tokens=0)
    cached = estimate_cost_usd(
        SONNET_4_7, input_tokens=0, output_tokens=0, cache_read_tokens=1000
    )
    assert cached < fresh / 5  # at least 5x cheaper


def test_fallback_ids_set():
    assert SONNET_4_7.fallback_id == "claude-sonnet-4-6"
    assert OPUS_4_7.fallback_id == "claude-opus-4-6"
    assert HAIKU_4_5.fallback_id is None  # cheapest tier — no fallback
