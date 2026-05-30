"""Kill-switch behavior of OpenRouterClient."""
from app.llm.client import get_llm_client
from app.llm.router import ModelTier


async def test_kill_switch_returns_mock():
    cli = get_llm_client()
    r = await cli.complete(
        agent="test",
        system="be terse",
        messages=[{"role": "user", "content": "hi"}],
        tier=ModelTier.cheap,
        max_tokens=32,
    )
    assert r.cost_usd == 0.0
    assert r.model.startswith("mock-")


async def test_kill_switch_json_mode_returns_dict():
    cli = get_llm_client()
    r = await cli.complete(
        agent="test",
        system="json",
        messages=[{"role": "user", "content": "give json"}],
        tier=ModelTier.cheap,
        max_tokens=32,
        json_mode=True,
    )
    assert r.json_payload is not None
    assert r.json_payload.get("_mock") is True
