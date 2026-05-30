# Quick Reference: Agent Briefs

This is a concise, high-level summary of all agents in the Parallax political platform.

---

## 1. SGA — Source Gathering Agent
* **Role:** Gathers and filters relevant web sources for a given situation.
* **Pipeline:** LLM query proposal (cheap tier) → Sequential EXA searches → Rank & Deduplicate → LLM source selection (default tier).
* **Cost Cap:** $0.08  
* **Inputs:** `situation_prompt`, optional `subject_slug`  
* **Outputs:** `SourcePack` (top 8 sources, query, coverage gaps)

---

## 2. DCAA — Domain Context Aware Agent
* **Role:** Analyzes institutional, legal, and conceptual contexts of a situation in the Philippines.
* **Pipeline:** Single LLM call (default tier) parsing domain briefing.
* **Cost Cap:** $0.08  
* **Inputs:** `situation_prompt`, upstream `SGA` sources  
* **Outputs:** `DomainBriefing` (concepts, constraints, precedents, risk flags, notes)

---

## 3. DEMCAA — Demographic Context Aware Agent
* **Role:** Profiles demographic cohorts affected by or relevant to the situation.
* **Pipeline:** Single LLM call (default tier) building demographic briefings and cohort models.
* **Cost Cap:** $0.08  
* **Inputs:** `situation_prompt`, upstream `SGA` sources  
* **Outputs:** `DemographicBriefing` (region, cohorts with share/issues/media mix, notes)

---

## 4. Strategist Agent
* **Role:** Synthesizes upstream context into tactical advice (perception map & action recommendations).
* **Pipeline:** First-pass LLM (default tier) → Auto-escalates to Opus (escalate tier) if confidence is low (< 0.6) → Fallbacks to hard safety hold if both fail.
* **Cost Cap:** $0.30  
* **Inputs:** `situation_prompt`, upstream `SGA` + `DCAA` + `DEMCAA` briefs  
* **Outputs:** `PerceptionMap` (emotions, dimensions, rationale) and `ActionCard` (who, what, where, when, how, avoid, success KPIs)

---

## 5. DisambiguationAgent
* **Role:** Stateless identity matching query tool.
* **Pipeline:** 2 EXA searches → LLM candidate card generation (cheap tier).
* **Cost Target:** ~$0.02  
* **Inputs:** fuzzy `name_query`, optional `hint`  
* **Outputs:** `IdentityCandidate` (full name, birthplace, role, bio, photo URL, confidence, ambiguity notes)

---

## 6. PIDAA — Person Identity Deep Analyzer Agent
* **Role:** Compiles a comprehensive 11-section identity dossier for a confirmed political figure.
* **Pipeline:** 8-facet EXA search → Top 40 ranked sources → 4 sequential LLM calls (default tier) for section groups A-D → DB persistence to `PrincipalIdentity`.
* **Cost Cap:** $0.50  
* **Inputs:** confirmed candidate details, profile UUID  
* **Outputs:** `PrincipalIdentityArtifact` (dossier with basics, family, education, timeline, position, party, elections, policies, voice, controversies, network)

---

## 7. SRCA — Source Real Check Agent (Utility)
* **Role:** Fast-checks URLs to prevent AI source fabrication by validating reachability and content presence.
* **Pattern:** Utility service (importable module), not a BaseAgent — agents call `validate_url()` or `validate_urls()` explicitly.
* **No Cost Cap:** Uses HTTP requests only (no LLM calls).
* **Inputs:** `list[str]` of URLs to validate  
* **Outputs:** `list[URLValidationResult]` with `is_valid`, `status_code`, `error`, `trusted_domain` flags
* **Usage:** Import from `app.utils.src_validator` — call before consuming sources from LLM outputs or external searches
