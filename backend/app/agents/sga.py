"""SGA — Source Gathering Agent.

Pipeline:
1. Ask the LLM (cheap tier) to propose 3–6 EXA queries for the situation.
2. Run EXA for each (with built-in 24h cache + daily quota).
3. Pool, dedupe by URL, sort by credibility × relevance.
4. Ask the LLM (default tier) to select the top N and identify coverage gaps.
5. Emit `SourcePack` artifact.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from app.agents._helpers import identity_brief, identity_query_seeds
from app.agents.base import AgentContext, BaseAgent
from app.llm.client import get_llm_client
from app.llm.prompts import load_prompt
from app.llm.router import ModelTier
from app.schemas.agents import AgentResult, EvidenceRef, SourceItem, SourcePack
from app.search.exa import ExaSearchResult, get_exa_client


class SGA(BaseAgent):
    name = "SGA"
    default_tier = ModelTier.default
    max_cost_usd = 0.08

    async def _run(self, ctx: AgentContext) -> AgentResult:
        llm = get_llm_client()
        exa = get_exa_client()
        system = load_prompt("sga", pack_id=ctx.pack_id)

        # --- 1. Retrieve live evidence from identity-derived queries ----------
        # Query-planning is intentionally skipped here: it adds a serial model
        # round-trip before retrieval without improving the brief's evidence base.
        seeds = identity_query_seeds(ctx)
        id_digest = identity_brief(ctx, max_chars=1200)
        proposed = [str(query).strip() for query in seeds if str(query).strip()][:3]
        if not proposed:
            raise ValueError("Brief source gathering requires a confirmed principal name")

        # --- 2. Run EXA --------------------------------------------------------
        pool: dict[str, ExaSearchResult] = {}

        async def search_query(query: str) -> list[ExaSearchResult]:
            try:
                return await exa.search(query, num_results=6)
            except Exception as exc:
                self.log.warning("sga.exa.error", query=query, error=str(exc))
                return []

        for results in await asyncio.gather(*(search_query(query) for query in proposed)):
            for result in results:
                pool.setdefault(result.url, result)

        ranked = sorted(
            pool.values(),
            key=lambda r: r.credibility_score * (r.score if r.score is not None else 0.5),
            reverse=True,
        )[:25]

        # --- 3. LLM selection + gap analysis ----------------------------------
        candidates_payload = [
            {
                "url": r.url,
                "title": r.title,
                "domain": r.domain,
                "published_at": r.published_at,
                "excerpt": r.excerpt,
                "credibility_score": round(r.credibility_score, 2),
            }
            for r in ranked
        ]
        select_msg: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": (
                    f"Principal identity digest:\n{id_digest}\n\n"
                    f"Queries used: {proposed}\n\n"
                    f"Candidate sources (already ranked by credibility×relevance):\n"
                    f"{json.dumps(candidates_payload, ensure_ascii=False)}\n\n"
                    "Pick the top 8 most decision-relevant sources for an upcoming brief. "
                    "Identify coverage_gaps. Return the JSON object defined in the system prompt."
                ),
            }
        ]
        sresp = await llm.complete(
            agent=self.name,
            system=system,
            messages=select_msg,
            tier=ModelTier.default,
            max_tokens=900,
            run_id=ctx.run_id,
            json_mode=True,
            temperature=0.2,
        )
        sel = sresp.json_payload or {}

        selected_raw = sel.get("selected")
        if not isinstance(selected_raw, list):
            raise ValueError("LLM returned no source selection")
        valid_urls = {c["url"] for c in candidates_payload}
        sources: list[SourceItem] = []
        for s in selected_raw:
            url = s.get("url")
            if not url or url not in valid_urls:
                continue  # reject invented urls
            base = next((c for c in candidates_payload if c["url"] == url), None)
            if base is None:
                continue
            sources.append(
                SourceItem(
                    url=url,
                    title=s.get("title") or base.get("title"),
                    domain=base["domain"],
                    published_at=s.get("published_at") or base.get("published_at"),
                    excerpt=s.get("excerpt") or base.get("excerpt"),
                    credibility_score=float(
                        s.get("credibility_score") or base.get("credibility_score") or 0.5
                    ),
                )
            )

        pack = SourcePack(
            query=" | ".join(proposed)[:200],
            sources=sources,
            coverage_gaps=sel.get("coverage_gaps") or [],
        )
        if not sources:
            raise ValueError("LLM selected no valid sources for the brief")

        evidence = [
            EvidenceRef(
                claim=f"Source surfaced by SGA: {s.title or s.url}",
                source_url=s.url,
                quote=s.excerpt,
                confidence=s.credibility_score,
            )
            for s in sources
        ]

        total_tokens_in = sresp.input_tokens
        total_tokens_out = sresp.output_tokens
        total_cost = sresp.cost_usd

        return AgentResult(
            agent=self.name,
            summary=(
                sel.get("summary")
                or f"Selected {len(sources)} sources across {len({s.domain for s in sources})} domains."
            ),
            payload=pack.model_dump(),
            evidence=evidence,
            tokens_in=total_tokens_in,
            tokens_out=total_tokens_out,
            cache_read_tokens=sresp.cache_read_tokens,
            cache_write_tokens=sresp.cache_write_tokens,
            cost_usd=round(total_cost, 6),
            model=sresp.model,
            confidence=min(1.0, 0.4 + 0.05 * len(sources)),
        )
