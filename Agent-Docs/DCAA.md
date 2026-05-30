# DCAA — Domain Context Aware Agent

**File:** `backend/app/agents/dcaa.py`  
**Class:** `DCAA(BaseAgent)`

---

## Purpose

Produces a `DomainBriefing` for the situation — surfacing relevant political/legal/institutional concepts, precedent cases, institutional constraints, and risk flags specific to the Philippine political domain. Runs after `SGA`, consuming its source pack as upstream context.

---

## Configuration

| Attribute | Value |
|-----------|-------|
| `name` | `"DCAA"` |
| `default_tier` | `ModelTier.default` |
| `max_cost_usd` | `$0.08` |

---

## Pipeline

```
1. Build user prompt from situation + subject + upstream brief
2. Single LLM call (default tier, JSON mode) → DomainBriefing JSON
3. Parse + validate into DomainBriefing schema
4. Emit AgentResult with EvidenceRef per risk flag
```

### LLM call parameters

| Parameter | Value |
|-----------|-------|
| `tier` | `ModelTier.default` |
| `max_tokens` | `1100` |
| `temperature` | `0.3` |
| `json_mode` | `True` |

---

## Output artifact — `DomainBriefing`

```json
{
  "relevant_concepts": ["..."],
  "institutional_constraints": ["..."],
  "precedent_cases": ["..."],
  "risk_flags": ["..."],
  "notes": "..."
}
```

Each entry in `risk_flags` is also emitted as an `EvidenceRef` with `confidence=0.6`.

---

## Confidence

Fixed at **0.65**.

---

## Context dependencies

| Dependency | Required | Notes |
|------------|----------|-------|
| `ctx.situation_prompt` | Yes | Core situation text |
| `ctx.subject_slug` | Optional | Included in user prompt as `Subject:` |
| `ctx.pack_id` | Optional | Selects system prompt via `load_prompt("dcaa")` |
| `ctx.upstream` | Optional | Summarised via `upstream_brief(ctx)` — expects `SGA` output |
