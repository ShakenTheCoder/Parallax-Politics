"""SCDRA — Specific Candidate Data Retrieval Agent.

Resolves coverage gaps detected by PIDAA through targeted EXA searches.
Triggered automatically when PIDAA identifies gaps in a principal's identity.

Pipeline:
1. Parse upstream PIDAA result → extract structured gaps
2. Filter to gaps meeting severity threshold
3. For each gap:
   a. Select retrieval strategy based on gap_type
   b. Build targeted EXA query using taxonomy templates
   c. Execute search → rank results
   d. LLM extraction call → structured field values
   e. Validate extracted data → provenance check
   f. Record attempt in gap_retrieval_attempts
4. Merge resolved fields into PrincipalIdentity
5. Recalculate data_completeness_score
6. Emit SCDRAArtifact with resolutions + remaining gaps
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select

from app.agents.base import AgentContext, BaseAgent
from app.db import session_scope
from app.identity import (
    GAP_TAXONOMY,
    GapType,
    calculate_data_completeness,
    get_gap_type,
)
from app.llm.client import get_llm_client
from app.llm.prompts import load_prompt
from app.llm.router import ModelTier
from app.models.gap_retrieval_attempt import GapRetrievalAttempt
from app.models.principal_identity import PrincipalIdentity
from app.schemas.agents import AgentResult, GapResolution, SCDRAArtifact
from app.search.exa import ExaSearchResult, get_exa_client

_DEFAULT_SEVERITY_THRESHOLD = "medium"  # Process medium and high severity gaps
_MAX_ATTEMPTS_PER_GAP = 3
_COST_BUDGET_PER_GAP_USD = 0.10


class SCDRA(BaseAgent):
    """Specific Candidate Data Retrieval Agent — fills identity coverage gaps."""

    name = "SCDRA"
    default_tier = ModelTier.default
    max_cost_usd = 0.30  # Overall run budget (covers multiple gaps)

    async def _run(self, ctx: AgentContext) -> AgentResult:
        llm = get_llm_client()
        system = load_prompt("scdra", pack_id=ctx.pack_id)
        exa = get_exa_client()

        # Get upstream PIDAA result
        pidaa_result = ctx.get("PIDAA")
        if not pidaa_result:
            return AgentResult(
                agent=self.name,
                summary="No PIDAA upstream result found; nothing to process.",
                payload={},
                confidence=0.0,
            )

        payload = pidaa_result.payload
        principal_identity_id = ctx.extra.get("profile_id")
        full_name = payload.get("full_name", "Unknown")

        # Get current gaps (prefer structured, fall back to converting legacy)
        gaps_data = payload.get("coverage_gaps_structured", [])
        if not gaps_data:
            # Try to convert legacy string gaps to structured
            gaps_data = self._convert_legacy_gaps(payload.get("coverage_gaps", []))

        # Filter gaps by severity threshold
        severity_order = {"high": 3, "medium": 2, "low": 1}
        threshold_value = severity_order.get(
            ctx.extra.get("scdra_severity_threshold", _DEFAULT_SEVERITY_THRESHOLD), 2
        )

        gaps_to_process = [
            g for g in gaps_data
            if severity_order.get(g.get("severity", "low"), 0) >= threshold_value
            and g.get("status") in ("pending", None)
            and g.get("auto_resolvable", True)
        ]

        if not gaps_to_process:
            return AgentResult(
                agent=self.name,
                summary=f"No gaps meeting severity threshold for {full_name}.",
                payload=SCDRAArtifact(
                    principal_identity_id=UUID(str(principal_identity_id)) if principal_identity_id else None,
                    gaps_processed=0,
                    gaps_resolved=0,
                    gaps_remaining=len(gaps_data),
                ).model_dump(),
                confidence=1.0,
            )

        # Track metrics
        cost_total = 0.0
        tokens_in_total = 0
        tokens_out_total = 0
        cache_r = 0
        cache_w = 0
        used_model = ""

        gaps_resolved = 0
        gaps_failed = 0
        resolutions: list[GapResolution] = []
        resolved_fields_map: dict[str, Any] = {}

        # Get identity sections for completeness calculation
        identity_sections = {
            "basics": payload.get("basics", {}),
            "family": payload.get("family", {}),
            "education": payload.get("education", {}),
            "career_timeline": payload.get("career_timeline", {}),
            "current_position": payload.get("current_position", {}),
            "party_history": payload.get("party_history", {}),
            "electoral_record": payload.get("electoral_record", {}),
            "policy_stances": payload.get("policy_stances", {}),
            "voice_signature": payload.get("voice_signature", {}),
            "controversies": payload.get("controversies", {}),
            "network": payload.get("network", {}),
        }

        completeness_before = calculate_data_completeness(identity_sections)

        # Process each gap
        for gap in gaps_to_process:
            gap_type_id = gap.get("gap_type", "unknown")
            gap_type = get_gap_type(gap_type_id)

            if not gap_type:
                self.log.warning("scdra.unknown_gap_type", gap_type=gap_type_id)
                continue

            # Check budget
            if cost_total + gap_type.cost_budget_usd > self.max_cost_usd:
                self.log.warning("scdra.budget_exhausted", gap_type=gap_type_id)
                break

            # Execute retrieval strategy
            attempt_result = await self._process_gap(
                gap=gap,
                gap_type=gap_type,
                full_name=full_name,
                identity_sections=identity_sections,
                system_prompt=system,
                llm=llm,
                exa=exa,
                principal_identity_id=principal_identity_id,
            )

            # Accumulate costs
            cost_total += attempt_result.get("cost_usd", 0)
            tokens_in_total += attempt_result.get("tokens_in", 0)
            tokens_out_total += attempt_result.get("tokens_out", 0)
            cache_r += attempt_result.get("cache_read_tokens", 0)
            cache_w += attempt_result.get("cache_write_tokens", 0)
            if attempt_result.get("model"):
                used_model = attempt_result["model"]

            # Track resolution
            if attempt_result.get("resolved"):
                gaps_resolved += 1
                gap["status"] = "resolved"
                for field_path, value in attempt_result.get("resolved_fields", {}).items():
                    resolutions.append(
                        GapResolution(
                            gap_type=gap_type_id,
                            fields_resolved=[field_path],
                            source_url=attempt_result.get("source_url"),
                            confidence=attempt_result.get("confidence", 0.7),
                        )
                    )
                    resolved_fields_map[field_path] = value
                    # Update identity sections for completeness recalculation
                    self._set_nested_field(identity_sections, field_path, value)
            else:
                gap["status"] = attempt_result.get("resolution_status", "failed")
                if attempt_result.get("resolution_status") == "failed":
                    gaps_failed += 1

        # Calculate new completeness
        completeness_after = calculate_data_completeness(identity_sections)

        # Persist updates to PrincipalIdentity if ID available
        if principal_identity_id:
            await self._persist_updates(
                principal_identity_id=UUID(str(principal_identity_id)),
                resolved_fields=resolved_fields_map,
                updated_gaps=gaps_data,
                completeness_score=completeness_after,
                scdra_cost=cost_total,
            )

        # Build artifact
        gaps_remaining = len([g for g in gaps_data if g.get("status") != "resolved"])

        artifact = SCDRAArtifact(
            principal_identity_id=UUID(str(principal_identity_id)) if principal_identity_id else None,
            run_timestamp=datetime.now(UTC),
            gaps_processed=len(gaps_to_process),
            gaps_resolved=gaps_resolved,
            gaps_remaining=gaps_remaining,
            resolutions=resolutions,
            data_completeness_before=completeness_before,
            data_completeness_after=completeness_after,
            total_cost_usd=round(cost_total, 6),
        )

        return AgentResult(
            agent=self.name,
            summary=f"SCDRA processed {len(gaps_to_process)} gaps for {full_name}: {gaps_resolved} resolved, {gaps_failed} failed, {gaps_remaining} remaining. Completeness: {completeness_before:.0%} → {completeness_after:.0%}",
            payload=artifact.model_dump(),
            tokens_in=tokens_in_total,
            tokens_out=tokens_out_total,
            cache_read_tokens=cache_r,
            cache_write_tokens=cache_w,
            cost_usd=round(cost_total, 6),
            model=used_model,
            confidence=0.75 if gaps_resolved > 0 else 0.5,
        )

    def _convert_legacy_gaps(self, legacy_gaps: list[str]) -> list[dict[str, Any]]:
        """Convert legacy string gap descriptions to structured format."""
        structured = []
        for gap_text in legacy_gaps:
            gap_type = self._infer_gap_type_from_text(gap_text)
            structured.append({
                "gap_type": gap_type.id if gap_type else "unknown",
                "severity": gap_type.severity if gap_type else "low",
                "description": gap_text,
                "affected_fields": list(gap_type.affected_sections) if gap_type else [],
                "auto_resolvable": gap_type.auto_resolvable if gap_type else True,
                "status": "pending",
            })
        return structured

    def _infer_gap_type_from_text(self, text: str) -> GapType | None:
        """Infer gap type from legacy description text."""
        text_lower = text.lower()

        # Map common patterns to gap types
        patterns = {
            "birth": "birth_record_missing",
            "birthdate": "birth_record_missing",
            "psa": "birth_record_missing",
            "education": "education_unverified",
            "degree": "education_unverified",
            "university": "education_unverified",
            "college": "education_unverified",
            "convert": "religion_conversion_unconfirmed",
            "islam": "religion_conversion_unconfirmed",
            "christianity": "religion_conversion_unconfirmed",
            "children": "family_children_incomplete",
            "sons": "family_children_incomplete",
            "daughters": "family_children_incomplete",
            "siblings": "siblings_details_missing",
            "brother": "siblings_details_missing",
            "sister": "siblings_details_missing",
            "mother": "mother_biography_missing",
            "votes": "electoral_votes_missing",
            "election": "electoral_votes_missing",
            "comelec": "electoral_votes_missing",
            "term": "term_dates_incomplete",
            "oath": "term_dates_incomplete",
            "sworn": "term_dates_incomplete",
            "policy": "policy_direct_quote_missing",
            "stance": "policy_direct_quote_missing",
            "statement": "policy_direct_quote_missing",
            "controversy": "controversy_legal_status_unknown",
            "case": "controversy_legal_status_unknown",
            "court": "controversy_legal_status_unknown",
            "party switch": "party_switch_date_unknown",
            "affiliation": "party_switch_date_unknown",
        }

        for pattern, gap_type_id in patterns.items():
            if pattern in text_lower:
                return get_gap_type(gap_type_id)

        return None

    async def _process_gap(
        self,
        gap: dict[str, Any],
        gap_type: GapType,
        full_name: str,
        identity_sections: dict[str, Any],
        system_prompt: str,
        llm: Any,
        exa: Any,
        principal_identity_id: Any,
    ) -> dict[str, Any]:
        """Process a single gap: search, extract, validate."""
        gap_type_id = gap.get("gap_type", "unknown")
        description = gap.get("description", "")
        affected_fields = gap.get("affected_fields", [])

        # Build search query
        query_params = self._extract_query_params(gap, identity_sections)
        search_query = gap_type.build_query(full_name, **query_params)

        self.log.info("scdra.searching", gap_type=gap_type_id, query=search_query)

        try:
            # Execute EXA search
            results = await exa.search(search_query, num_results=5, text_chars=800)
        except Exception as exc:
            self.log.warning("scdra.search_failed", gap_type=gap_type_id, error=str(exc))
            await self._record_attempt(
                principal_identity_id=principal_identity_id,
                gap_type=gap_type_id,
                gap_severity=gap_type.severity,
                attempt_number=1,
                strategy="exa_search",
                search_query=search_query,
                sources_found=[],
                resolution_status="failed",
                resolved_fields=[],
                cost_usd=0.0,
            )
            return {"resolved": False, "resolution_status": "failed", "cost_usd": 0.0}

        if not results:
            await self._record_attempt(
                principal_identity_id=principal_identity_id,
                gap_type=gap_type_id,
                gap_severity=gap_type.severity,
                attempt_number=1,
                strategy="exa_search",
                search_query=search_query,
                sources_found=[],
                resolution_status="failed",
                resolved_fields=[],
                cost_usd=0.0,
            )
            return {"resolved": False, "resolution_status": "failed", "cost_usd": 0.0}

        # Rank and select best source
        best_source = results[0]  # Already sorted by credibility * score

        # Build extraction prompt
        extraction_prompt = self._build_extraction_prompt(
            gap_type_id=gap_type_id,
            description=description,
            affected_fields=affected_fields,
            full_name=full_name,
            source_title=best_source.title or "",
            source_url=best_source.url,
            source_excerpt=best_source.excerpt or "",
        )

        # Execute LLM extraction
        try:
            resp = await llm.complete(
                agent=self.name,
                system=system_prompt,
                messages=[{"role": "user", "content": extraction_prompt}],
                tier=ModelTier.default,
                max_tokens=800,
                run_id=None,  # SCDRA runs as sub-process
                json_mode=True,
                temperature=0.2,
            )
        except Exception as exc:
            self.log.warning("scdra.extraction_failed", gap_type=gap_type_id, error=str(exc))
            await self._record_attempt(
                principal_identity_id=principal_identity_id,
                gap_type=gap_type_id,
                gap_severity=gap_type.severity,
                attempt_number=1,
                strategy="exa_search",
                search_query=search_query,
                sources_found=[self._source_to_dict(s) for s in results],
                resolution_status="failed",
                resolved_fields=[],
                cost_usd=0.0,
            )
            return {"resolved": False, "resolution_status": "failed", "cost_usd": 0.0}

        # Parse extraction result
        extraction_data = resp.json_payload or {}
        resolved_fields = extraction_data.get("resolved_fields", {})
        confidence = extraction_data.get("confidence", 0.0)
        found_data = extraction_data.get("found", False)

        # Validate: need at least one field resolved with reasonable confidence
        if not found_data or not resolved_fields or confidence < 0.5:
            await self._record_attempt(
                principal_identity_id=principal_identity_id,
                gap_type=gap_type_id,
                gap_severity=gap_type.severity,
                attempt_number=1,
                strategy="exa_search",
                search_query=search_query,
                sources_found=[self._source_to_dict(s) for s in results],
                resolution_status="failed",
                resolved_fields=[],
                cost_usd=resp.cost_usd,
            )
            return {
                "resolved": False,
                "resolution_status": "failed",
                "cost_usd": resp.cost_usd,
                "tokens_in": resp.input_tokens,
                "tokens_out": resp.output_tokens,
                "cache_read_tokens": resp.cache_read_tokens,
                "cache_write_tokens": resp.cache_write_tokens,
                "model": resp.model,
            }

        # Success - record the resolution
        await self._record_attempt(
            principal_identity_id=principal_identity_id,
            gap_type=gap_type_id,
            gap_severity=gap_type.severity,
            attempt_number=1,
            strategy="exa_search",
            search_query=search_query,
            sources_found=[self._source_to_dict(s) for s in results],
            resolution_status="resolved",
            resolved_fields=list(resolved_fields.keys()),
            cost_usd=resp.cost_usd,
        )

        return {
            "resolved": True,
            "resolution_status": "resolved",
            "resolved_fields": resolved_fields,
            "source_url": best_source.url,
            "confidence": confidence,
            "cost_usd": resp.cost_usd,
            "tokens_in": resp.input_tokens,
            "tokens_out": resp.output_tokens,
            "cache_read_tokens": resp.cache_read_tokens,
            "cache_write_tokens": resp.cache_write_tokens,
            "model": resp.model,
        }

    def _extract_query_params(self, gap: dict[str, Any], identity_sections: dict[str, Any]) -> dict[str, Any]:
        """Extract context-specific parameters for query templates."""
        params = {}
        gap_type_id = gap.get("gap_type", "")
        affected_fields = gap.get("affected_fields", [])

        # Extract education institution if available
        if "education" in gap_type_id and affected_fields:
            education = identity_sections.get("education", {})
            degrees = education.get("degrees", [])
            if degrees and degrees[0].get("institution"):
                params["institution"] = degrees[0]["institution"]

        # Extract birthplace if available
        if "birth" in gap_type_id:
            basics = identity_sections.get("basics", {})
            if basics.get("birthplace"):
                params["birthplace"] = basics["birthplace"]

        # Extract policy topic
        if "policy" in gap_type_id and affected_fields:
            # Extract policy key from affected_fields like "policy_stances.wps_south_china_sea"
            for field in affected_fields:
                if "policy_stances." in field:
                    policy_key = field.split(".")[-1]
                    params["policy_topic"] = policy_key.replace("_", " ")

        # Extract election year
        if "electoral" in gap_type_id:
            electoral = identity_sections.get("electoral_record", {})
            races = electoral.get("races", [])
            if races:
                params["year"] = races[0].get("year", "")
                params["office"] = races[0].get("office", "")

        # Extract controversy label
        if "controversy" in gap_type_id:
            controversies = identity_sections.get("controversies", {})
            items = controversies.get("items", [])
            if items:
                params["controversy_label"] = items[0].get("label", "controversy")

        # Extract role
        if "term" in gap_type_id:
            current = identity_sections.get("current_position", {})
            params["role"] = current.get("role", "")

        # Extract party info
        if "party" in gap_type_id:
            party = identity_sections.get("party_history", {})
            affiliations = party.get("affiliations", [])
            if len(affiliations) >= 2:
                params["old_party"] = affiliations[0].get("party", "")
                params["new_party"] = affiliations[-1].get("party", "")

        # Extract ally/rival names
        if "network" in gap_type_id:
            network = identity_sections.get("network", {})
            allies = network.get("allies", [])
            rivals = network.get("rivals", [])
            if allies:
                params["ally_name"] = allies[0].get("name", "")
            if rivals:
                params["rival_name"] = rivals[0].get("name", "")

        return params

    def _build_extraction_prompt(
        self,
        gap_type_id: str,
        description: str,
        affected_fields: list[str],
        full_name: str,
        source_title: str,
        source_url: str,
        source_excerpt: str,
    ) -> str:
        """Build the LLM prompt for data extraction."""
        return f"""Gap to resolve: {gap_type_id}
Description: {description}
Principal: {full_name}
Target fields: {', '.join(affected_fields)}

Source to extract from:
Title: {source_title}
URL: {source_url}
Excerpt:
{source_excerpt}

Extract the requested information from the source above. Return a JSON object:
{{
  "found": true/false,
  "confidence": 0.0-1.0,
  "resolved_fields": {{
    "field.path": "extracted value",
    ...
  }},
  "reasoning": "brief explanation"
}}

Rules:
- Only include fields where you found explicit evidence in the source
- Set confidence 0.9+ if directly stated, 0.7-0.8 if strongly implied, 0.5-0.6 if weakly implied
- Never invent information not present in the source
- If information not found, return "found": false and empty resolved_fields
"""

    def _source_to_dict(self, source: ExaSearchResult) -> dict[str, Any]:
        """Convert ExaSearchResult to dict for storage."""
        return {
            "url": source.url,
            "title": source.title,
            "domain": source.domain,
            "credibility_score": source.credibility_score,
            "score": source.score,
        }

    def _set_nested_field(self, data: dict[str, Any], field_path: str, value: Any) -> None:
        """Set a value in nested dict using dot notation like 'basics.born'."""
        parts = field_path.split(".")
        current = data

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    async def _record_attempt(
        self,
        principal_identity_id: Any,
        gap_type: str,
        gap_severity: str,
        attempt_number: int,
        strategy: str,
        search_query: str,
        sources_found: list[dict[str, Any]],
        resolution_status: str,
        resolved_fields: list[str],
        cost_usd: float,
    ) -> None:
        """Record a retrieval attempt to the database."""
        if not principal_identity_id:
            return

        try:
            async with session_scope() as db:
                attempt = GapRetrievalAttempt(
                    principal_identity_id=UUID(str(principal_identity_id)),
                    gap_type=gap_type,
                    gap_severity=gap_severity,
                    attempt_number=attempt_number,
                    strategy=strategy,
                    search_query=search_query,
                    sources_found=sources_found,
                    resolution_status=resolution_status,
                    resolved_fields=resolved_fields,
                    cost_usd=cost_usd,
                )
                db.add(attempt)
        except Exception as exc:
            self.log.warning("scdra.record_attempt_failed", error=str(exc))

    async def _persist_updates(
        self,
        principal_identity_id: UUID,
        resolved_fields: dict[str, Any],
        updated_gaps: list[dict[str, Any]],
        completeness_score: float,
        scdra_cost: float,
    ) -> None:
        """Persist resolved fields and updated gaps to PrincipalIdentity."""
        try:
            async with session_scope() as db:
                res = await db.execute(
                    select(PrincipalIdentity).where(
                        PrincipalIdentity.profile_id == principal_identity_id
                    )
                )
                pi = res.scalar_one_or_none()
                if not pi:
                    self.log.warning("scdra.principal_not_found", profile_id=str(principal_identity_id))
                    return

                # Merge resolved fields into identity sections
                for field_path, value in resolved_fields.items():
                    self._merge_field_into_principal(pi, field_path, value)

                # Update structured gaps
                pi.coverage_gaps_structured = updated_gaps

                # Update tracking columns
                pi.scdra_runs = (pi.scdra_runs or 0) + 1
                pi.scdra_last_run = datetime.now(UTC)
                pi.data_completeness_score = completeness_score

                # Note: We don't update coverage_gaps (legacy) to preserve history

        except Exception as exc:
            self.log.warning("scdra.persist_failed", error=str(exc))

    def _merge_field_into_principal(self, pi: PrincipalIdentity, field_path: str, value: Any) -> None:
        """Merge a resolved field value into the PrincipalIdentity model."""
        # Map field paths to model columns
        section_map = {
            "basics.": "basics",
            "family.": "family",
            "education.": "education",
            "career_timeline.": "career_timeline",
            "current_position.": "current_position",
            "party_history.": "party_history",
            "electoral_record.": "electoral_record",
            "policy_stances.": "policy_stances",
            "voice_signature.": "voice_signature",
            "controversies.": "controversies",
            "network.": "network",
        }

        # Determine which section this field belongs to
        target_section = None
        for prefix, section_name in section_map.items():
            if field_path.startswith(prefix):
                target_section = section_name
                inner_path = field_path[len(prefix):]
                break

        if not target_section:
            return

        # Get current section data
        section_data = getattr(pi, target_section, {}) or {}

        # Set the field
        self._set_nested_field(section_data, inner_path, value)

        # Update the model
        setattr(pi, target_section, section_data)
