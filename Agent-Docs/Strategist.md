# Strategist Agent

**File:** `backend/app/agents/strategist.py`  
**Class:** `Strategist(BaseAgent)`

---

## Purpose

Terminal agent in the main situation pipeline. Consumes all upstream outputs (`SGA`, `DCAA`, `DEMCAA`) and produces a `PerceptionMap` (how target audiences perceive the principal) plus an `ActionCard` (concrete recommended action). Includes automatic escalation to a higher-capability model tier when confidence is low.

---

## Configuration

| Attribute | Value |
|-----------|-------|
| `name` | `"Strategist"` |
| `default_tier` | `ModelTier.default` |
| `max_cost_usd` | `$0.30` |

---

## Pipeline

```
1. First-pass LLM call (default tier) → JSON with perception_map + action_card
2. Parse + validate via _parse()
3. If confidence < 0.6 OR parse failed → escalate to ModelTier.escalate (Opus)
4. Accept escalated result only if it improves confidence
5. If both passes fail → emit hard fallback ("Hold" card)
6. Emit AgentResult
```

### First-pass LLM call

| Parameter | Value |
|-----------|-------|
| `tier` | `ModelTier.default` |
| `max_tokens` | `2200` |
| `temperature` | `0.4` |
| `json_mode` | `True` |

Upstream context injected via `upstream_brief(ctx, max_chars=7000)`.

### Escalation

Triggered when `parsed is None` or `action_card.confidence < 0.6`.

| Parameter | Value |
|-----------|-------|
| `tier` | `ModelTier.escalate` |
| `max_tokens` | `2400` |
| `temperature` | `0.3` |

The prior assistant turn is included in the message history with a re-derive instruction. If `BudgetExhaustedError` is raised, escalation is skipped with a warning log and the first-pass result is used.

---

## Output artifact — `PerceptionMap` + `ActionCard`

```json
{
  "perception_map": {
    "emotions": { "<emotion_key>": 0.0 },
    "dimensions": { "<dimension_key>": 0.0 },
    "weakest_dimension": "...",
    "rationale": "..."
  },
  "action_card": {
    "what": "...",
    "who": "...",
    "where": "...",
    "when": "...",
    "how": "...",
    "proof": "...",
    "avoid": "...",
    "confidence": 0.0–1.0,
    "success_kpis": ["..."]
  }
}
```

Emotion and dimension keys are driven by the active context pack (`pack.emotions`, `pack.dimensions`).

---

## Hard Fallback

If parsing fails on both passes, a neutral `PerceptionMap` (all scores `0.0`) and a conservative `ActionCard` are emitted:

- **what:** `"Hold — do not engage publicly in the next 6 hours."`
- **confidence:** `0.3`

---

## Confidence

Set to `action_card.confidence` from the winning parse (or `0.3` for the hard fallback).

---

## Context dependencies

| Dependency | Required | Notes |
|------------|----------|-------|
| `ctx.situation_prompt` | Yes | Primary analysis input |
| `ctx.subject_slug` | Optional | Included in user prompt as `Subject:` |
| `ctx.pack_id` | Optional | Selects system prompt + emotion/dimension schema |
| `ctx.upstream` | Expected | Should contain `SGA`, `DCAA`, `DEMCAA` results |
