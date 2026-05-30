# DEMCAA — Demographic Context Aware Agent

**File:** `backend/app/agents/demcaa.py`  
**Class:** `DEMCAA(BaseAgent)`

---

## Purpose

Produces a `DemographicBriefing` for the situation — profiling the key Philippine demographic cohorts relevant to the situation, including their population share, salient issues, and media consumption mix. Runs in parallel with `DCAA` after `SGA`.

---

## Configuration

| Attribute | Value |
|-----------|-------|
| `name` | `"DEMCAA"` |
| `default_tier` | `ModelTier.default` |
| `max_cost_usd` | `$0.08` |

---

## Pipeline

```
1. Build user prompt from situation + subject + upstream brief
2. Single LLM call (default tier, JSON mode) → DemographicBriefing JSON
3. Parse cohorts; skip any cohort missing a "name" field
4. Emit AgentResult
```

### LLM call parameters

| Parameter | Value |
|-----------|-------|
| `tier` | `ModelTier.default` |
| `max_tokens` | `1100` |
| `temperature` | `0.3` |
| `json_mode` | `True` |

---

## Output artifact — `DemographicBriefing`

```json
{
  "region": "Philippines",
  "cohorts": [
    {
      "name": "...",
      "share_pct": 0.0–100.0,
      "salient_issues": ["..."],
      "media_mix": {
        "TV": 0.0,
        "Facebook": 0.0,
        "TikTok": 0.0
      }
    }
  ],
  "notes": "..."
}
```

`region` defaults to `"Philippines"` if the LLM omits it.  
`media_mix` values are cast to `float`; non-numeric entries are silently dropped.  
Cohorts with no `name` field are skipped.

---

## Confidence

Fixed at **0.60**.

---

## Context dependencies

| Dependency | Required | Notes |
|------------|----------|-------|
| `ctx.situation_prompt` | Yes | Core situation text |
| `ctx.subject_slug` | Optional | Included in user prompt as `Subject:` |
| `ctx.pack_id` | Optional | Selects system prompt via `load_prompt("demcaa")` |
| `ctx.upstream` | Optional | Summarised via `upstream_brief(ctx)` — expects `SGA` output |
