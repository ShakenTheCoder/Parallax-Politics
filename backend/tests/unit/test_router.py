from app.llm.router import LLAMA_3_3_70B, ModelTier, estimate_cost_usd, pick_model


def test_pick_model_tiers():
    assert pick_model(ModelTier.cheap, provider="nvidia") is LLAMA_3_3_70B
    assert pick_model(ModelTier.default, provider="nvidia") is LLAMA_3_3_70B
    assert pick_model(ModelTier.escalate, provider="nvidia") is LLAMA_3_3_70B


def test_ollama_provider_uses_the_local_registry():
    assert pick_model(ModelTier.cheap, provider="ollama").family == "ollama-local"


def test_cost_estimate_known_rates():
    cost = estimate_cost_usd(LLAMA_3_3_70B, input_tokens=1_000, output_tokens=1_000)
    assert cost == 0.0


def test_cache_read_is_cheaper_than_input():
    fresh = estimate_cost_usd(LLAMA_3_3_70B, input_tokens=1000, output_tokens=0)
    cached = estimate_cost_usd(
        LLAMA_3_3_70B, input_tokens=0, output_tokens=0, cache_read_tokens=1000
    )
    assert cached == fresh == 0.0


def test_registered_model_is_the_nvidia_model():
    assert LLAMA_3_3_70B.id == "meta/llama-3.3-70b-instruct"
