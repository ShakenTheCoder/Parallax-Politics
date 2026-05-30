# Agent Docs — Parallax Politics Backend

This folder contains documentation for every agent in `backend/app/agents/`.

| File | Agent | Role |
|------|-------|------|
| [brief.md](./brief.md) | **All Agents** | **Quick-reference summary (brief)** |
| [base.md](./base.md) | `BaseAgent` / `AgentContext` | Shared lifecycle, context contract |
| [SGA.md](./SGA.md) | `SGA` | Source Gathering Agent |
| [DCAA.md](./DCAA.md) | `DCAA` | Domain Context Aware Agent |
| [DEMCAA.md](./DEMCAA.md) | `DEMCAA` | Demographic Context Aware Agent |
| [PIDAA.md](./PIDAA.md) | `PIDAA` | Person Identity Deep Analyzer Agent |
| [SCDRA.md](./SCDRA.md) | `SCDRA` | Specific Candidate Data Retrieval Agent (gap resolution) |
| [Strategist.md](./Strategist.md) | `Strategist` | Perception + Action strategist |
| [DisambiguationAgent.md](./DisambiguationAgent.md) | `DisambiguationAgent` | Identity disambiguation step |
| [SRCA.md](./SRCA.md) | `SRCA` | Source Real Check Agent (URL validation utility) |

## Typical Run Order

```
SGA → DCAA + DEMCAA (parallel) → Strategist
```

`PIDAA`, `SCDRA`, and `DisambiguationAgent` are invoked separately, outside the main situation pipeline, during principal-creation flows:

```
DisambiguationAgent → PIDAA → SCDRA (auto-triggered if gaps exist)
```
