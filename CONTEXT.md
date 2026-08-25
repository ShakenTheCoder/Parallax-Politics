# Parallax Political Intelligence

Parallax turns authorized public evidence and representative research into reviewable campaign intelligence for one exclusive Philippine client.

## Language

**Principal**:
The signed-in public figure or authorized campaign whose work is scoped to the platform. Do not call a person a 2028 candidate without authoritative declaration or filing evidence.
_Avoid_: User candidate, principal candidate when status is unverified

**Watchlist Figure**:
A public figure monitored from authorized public sources because a cited poll placed them in the same hypothetical race, or because a later official ballot record does so.
_Avoid_: Candidate, target, tracked person when filing status is unverified

**Signal**:
A time-stamped, provenance-bearing public observation such as a statement, article, post, engagement count, or poll result.
_Avoid_: Raw data, scraped item

**Narrative**:
A time-bounded cluster of related public claims, themes, and reactions supported by Signals.
_Avoid_: Story, topic

**Cohort**:
A non-identifiable aggregate population group large enough to satisfy the platform's privacy threshold.
_Avoid_: Persona, voter profile, microtarget

**Synthetic Archetype**:
An explicitly artificial qualitative lens backed by an aggregate Cohort and three parallel samples. It is never polling, voter intent, individual prediction, or a target segment.
_Avoid_: Synthetic voter, persuadable, best segment

**Estimate**:
A model-produced analytical result with explicit uncertainty, assumptions, evidence, and validity period.
_Avoid_: Prediction, fact

**Scenario**:
A controlled comparison of a proposed public action or message against a frozen evidence context.
_Avoid_: Experiment, intervention

**Verdict**:
A strategic recommendation that has passed evidence, compliance, critic, and authorized analyst review.
_Avoid_: AI answer, automatic recommendation

**Context Pack**:
A versioned, time-bounded evidence bundle supplied to an analytical agent without information newer than its effective time.
_Avoid_: Prompt context, memory dump

## Product invariants

- The next regular presidential election is expected on May 8, 2028 under the constitutional/statutory cycle; the detailed COMELEC calendar remains pending. October 2026 is not a presidential election.
- The initial six-person research watchlist is sourced to Pulse Asia's July 2026 hypothetical long list. All six retain `polled_hypothetical` until stronger, dated evidence supports another status.
- Campaign Momentum includes observed performance and authorized owned analytics only. Polling and synthetic simulation are separate evidence layers. Competitive rank is suppressed below 60% coverage confidence.
- Competitor relationships are mechanical same-question or same-ballot links with profile IDs, effective dates, and evidence. LLM output cannot authoritatively create a rival, candidacy, or party-affiliation record.
- `/brief` is the mobile-first 30-second Brief. `/analysis` is reserved for the planned Analysis Center; until that experience is specified, it renders only its route shell. `/audience` redirects there.
- Brief never substitutes fixture metrics. Missing scores, appearances, and opinions render as unavailable until provenance-bearing snapshots exist.

- PIDAA and Brief content is generated from retrieved evidence and LLM analysis. The product must fail visibly when that evidence or analysis is unavailable; it must not substitute templates or fabricated defaults.
- A brief must retain the source URLs it relied on. Its reasoning must distinguish evidence gaps from conclusions.
- Briefs are append-only decision records. Archiving removes a brief from the active experience without deleting the underlying audit record.
- Principal intelligence must address audience perspective, message positioning, and the competitive landscape, with uncertainty made explicit where evidence is incomplete.
- A Brief has a bounded live-analysis window. Provider calls and the full run time out visibly rather than remaining in an ambiguous running state; only one active Brief run may be presented per principal.
