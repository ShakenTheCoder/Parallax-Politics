from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx

from app.agents.base import AgentContext, BaseAgent
from app.config import get_settings
from app.llm.client import get_llm_client
from app.llm.router import ModelTier
from app.schemas.agents import AgentResult
from app.schemas.audience import FacebookAnalysisResult

settings = get_settings()


class FacebookAnalysisAgent(BaseAgent):
    name = "FacebookAnalysis"
    default_tier = ModelTier.default
    max_cost_usd = 0.50

    async def _run(self, ctx: AgentContext) -> AgentResult:
        llm = get_llm_client()

        # 1. Gather inputs
        p_inst = ctx.upstream.get("PersonalAudience")
        comp_inst = ctx.upstream.get("CompetitorsAudience")
        ctx_inst = ctx.upstream.get("ContextualAudience")
        competitors_res = ctx.upstream.get("CompetitorAnalysis")

        if not settings.meta_access_token:
            raise RuntimeError("META_ACCESS_TOKEN is required for Facebook analysis")

        personal_data = await self._scrape_personal(p_inst)
        competitor_data = await self._scrape_competitors(comp_inst, competitors_res)
        contextual_data = await self._scrape_contextual(ctx_inst)

        # Combine raw data
        raw_graph_data = {
            "Personal": personal_data,
            "Competitors": competitor_data,
            "Contextual": contextual_data,
        }

        prompt_content = await asyncio.to_thread(
            Path("app/contexts/philippines_politics/agents/facebook_analysis.md").read_text
        )

        system_prompt = (
            prompt_content.split("---")[-1].strip() if "---" in prompt_content else prompt_content
        )

        user_content = (
            "Please analyze the following raw Facebook Graph API data and output the result according to the JSON schema.\n\n"
            f"```json\n{json.dumps(raw_graph_data, indent=2)}\n```"
        )

        resp = await llm.complete(
            agent=self.name,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
            tier=self.default_tier,
            max_tokens=3000,
            run_id=ctx.run_id,
            json_mode=True,
            temperature=0.3,
        )

        if resp.json_payload is None:
            raise ValueError("LLM returned no valid Facebook analysis JSON")
        parsed = FacebookAnalysisResult.model_validate(resp.json_payload)

        return AgentResult(
            agent=self.name,
            summary="Completed Facebook Graph API analysis for the principal, competitors, and context.",
            payload=parsed.model_dump(),
            tokens_in=resp.input_tokens,
            tokens_out=resp.output_tokens,
            cache_read_tokens=resp.cache_read_tokens,
            cache_write_tokens=resp.cache_write_tokens,
            cost_usd=resp.cost_usd,
            model=resp.model,
            confidence=0.85,
        )

    async def _fetch_graph_api(self, endpoint: str, params: dict) -> dict:
        """Helper to call Facebook Graph API."""
        url = f"https://graph.facebook.com/v20.0/{endpoint}"
        params["access_token"] = settings.meta_access_token
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, timeout=10.0)
            resp.raise_for_status()
            return resp.json()

    async def _scrape_personal(self, inst: AgentResult | None) -> dict:
        """Fetch posts from the principal page identified by the upstream artifact."""
        page_id = self._page_id(inst, "principal_page_id")
        return await self._fetch_graph_api(
            f"{page_id}/posts",
            {
                "fields": "message,created_time,shares,comments.summary(true),reactions.summary(true)"
            },
        )

    async def _scrape_competitors(
        self, inst: AgentResult | None, comp_res: AgentResult | None
    ) -> dict:
        page_ids = self._page_ids(comp_res, "competitor_page_ids")
        return {
            page_id: await self._fetch_graph_api(
                f"{page_id}/posts",
                {
                    "fields": "message,created_time,shares,comments.summary(true),reactions.summary(true)"
                },
            )
            for page_id in page_ids
        }

    async def _scrape_contextual(self, inst: AgentResult | None) -> dict:
        page_ids = self._page_ids(inst, "contextual_page_ids")
        return {
            page_id: await self._fetch_graph_api(
                f"{page_id}/feed",
                {"fields": "message,created_time,comments.summary(true),reactions.summary(true)"},
            )
            for page_id in page_ids
        }

    @staticmethod
    def _page_id(result: AgentResult | None, key: str) -> str:
        page_ids = FacebookAnalysisAgent._page_ids(result, key)
        if len(page_ids) != 1:
            raise ValueError(f"Exactly one {key} is required for Facebook analysis")
        return page_ids[0]

    @staticmethod
    def _page_ids(result: AgentResult | None, key: str) -> list[str]:
        if result is None:
            raise ValueError(f"Upstream artifact is required to resolve {key}")
        values = result.payload.get(key)
        if not isinstance(values, list) or not all(
            isinstance(value, str) and value for value in values
        ):
            raise ValueError(f"Upstream artifact must provide a non-empty {key} list")
        return values
