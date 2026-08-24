import asyncio
import time

import pytest

from app.agents.base import AgentContext
from app.agents.sga import SGA
from app.llm.client import LLMResponse
from app.search.exa import ExaSearchResult


class _SlowSearch:
    async def search(self, query: str, *, num_results: int) -> list[ExaSearchResult]:
        await asyncio.sleep(0.05)
        index = {
            "Sara Duterte latest news": 0,
            "Sara Duterte controversy": 1,
            "Sara Duterte statement this week": 2,
        }[query]
        return [
            ExaSearchResult(
                url=f"https://source.test/{index}",
                domain="source.test",
                title=f"Source {index}",
                published_at=None,
                excerpt="Live evidence excerpt",
                credibility_score=0.9,
            )
        ]


class _SelectingLLM:
    async def complete(self, **_: object) -> LLMResponse:
        return LLMResponse(
            text="",
            model="test-model",
            input_tokens=1,
            output_tokens=1,
            cache_read_tokens=0,
            cache_write_tokens=0,
            cost_usd=0.0,
            latency_ms=0,
            json_payload={
                "selected": [
                    {"url": "https://source.test/0"},
                    {"url": "https://source.test/1"},
                    {"url": "https://source.test/2"},
                ],
                "coverage_gaps": [],
            },
        )


@pytest.mark.asyncio
async def test_sga_retrieves_identity_queries_concurrently(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.agents.sga.get_exa_client", lambda: _SlowSearch())
    monkeypatch.setattr("app.agents.sga.get_llm_client", lambda: _SelectingLLM())
    ctx = AgentContext(
        run_id="run",
        situation_prompt="",
        extra={"full_name": "Sara Duterte"},
    )

    started = time.perf_counter()
    result = await SGA()._run(ctx)
    elapsed = time.perf_counter() - started

    assert elapsed < 0.13
    assert len(result.payload["sources"]) == 3
