# BaseAgent & AgentContext

**File:** `backend/app/agents/base.py`

---

## AgentContext

Shared per-run state passed into every agent's `_run` method.

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | `UUID \| str \| None` | Unique identifier for the current pipeline run |
| `situation_prompt` | `str` | The raw situation text driving the analysis |
| `subject_slug` | `str \| None` | URL-friendly identifier for the principal being analysed |
| `pack_id` | `str \| None` | Active context pack (controls prompts & dimension schema) |
| `upstream` | `dict[str, AgentResult]` | Results from agents that ran earlier in the pipeline |
| `extra` | `dict[str, Any]` | Arbitrary run-specific data (e.g. `confirmed_candidate`, `profile_id`) |

**Helper method**

```python
ctx.get("SGA")  # → AgentResult | None
```

Returns the upstream result for the named agent, or `None` if it hasn't run yet.

---

## BaseAgent

Abstract base class every agent extends.

### Class-level attributes (override per subclass)

| Attribute | Default | Description |
|-----------|---------|-------------|
| `name` | `"base"` | Registry ID used in logs, event bus, and DB writes |
| `default_tier` | `ModelTier.default` | LLM model tier used unless overridden at call-site |
| `max_cost_usd` | `0.20` | Per-run hard budget cap; exceeded calls raise `BudgetExhaustedError` |

### Public API

```python
await agent.run(ctx: AgentContext) -> AgentResult
```

Wraps `_run` with:
1. `agent.started` event published to the event bus.
2. Wall-clock timing.
3. `agent.completed` / `agent.failed` events with cost + latency metadata.

### Subclass contract

```python
async def _run(self, ctx: AgentContext) -> AgentResult:
    ...
```

Every concrete agent must implement `_run`. It must return an `AgentResult` and may raise freely — `run()` will catch, log, and re-raise.

---

## AgentResult schema

Defined in `app.schemas.agents`. Key fields:

| Field | Type | Notes |
|-------|------|-------|
| `agent` | `str` | Populated automatically by `run()` |
| `summary` | `str` | Human-readable one-liner for the run result |
| `payload` | `dict` | Agent-specific artifact (e.g. `SourcePack`, `DomainBriefing`) |
| `evidence` | `list[EvidenceRef]` | Supporting citations |
| `tokens_in` | `int` | Prompt tokens consumed |
| `tokens_out` | `int` | Completion tokens produced |
| `cache_read_tokens` | `int` | Tokens served from the LLM prompt cache |
| `cache_write_tokens` | `int` | Tokens written into the LLM prompt cache |
| `cost_usd` | `float` | Actual spend for this run |
| `model` | `str` | Model ID that produced the result |
| `confidence` | `float` | 0–1 self-reported confidence score |
