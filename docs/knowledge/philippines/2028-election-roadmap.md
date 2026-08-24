# 2028 election roadmap

**Source date:** 2026-08-24  
**Retrieval date:** 2026-08-24  
**Scope:** regular Philippine presidential-election cycle

## What is fixed and what is pending

| Milestone | Status | Evidence |
|---|---|---|
| Presidential term is six years | Fixed constitutional rule | [1987 Constitution, Article VII](https://lawphil.net/consti/cons1987.html) |
| President and vice-president elected together with synchronized national/local elections every six years | Fixed statutory cycle | [RA 7166, section 2](https://lawphil.net/statutes/repacts/ra1991/ra_7166_1991.html) |
| Expected regular election day: May 8, 2028 | Calculated from the second-Monday cycle | High confidence in calculation; official calendar pending |
| COC window, substitution deadlines, campaign periods, spending rules, prohibited-act periods, canvass calendar | Pending | Must come from a future COMELEC 2028 resolution and related issuances |

The product may show “Expected May 8, 2028” but must never represent the detailed calendar as final before COMELEC publishes it.

## Operational phases

1. **Baseline building — now through official-calendar publication.** Maintain the six-person `polled_hypothetical` watchlist, source catalog, historical polls, issue taxonomy, public-appearance archive, and coverage diagnostics.
2. **Watchlist monitoring — continuous.** Record offices, formal affiliations, attributable declarations, status history, and evidence gaps. A media headline alone cannot change legal status.
3. **COC publication — dates pending.** Ingest the official list and filing documents, link watchlist profiles mechanically, and change status to `filed_candidate` only with COMELEC evidence.
4. **Campaign period — dates pending.** Increase source cadence; freeze seven-day comparison windows; archive ad/message variants; maintain spending/rights controls and human review.
5. **Election day — expected May 8, 2028.** Freeze campaign recommendations, label results as unofficial until the competent canvassing body reports them, and preserve the evidence ledger.
6. **Canvassing and proclamation — dates pending.** Keep unofficial returns, canvass records, disputes, and official proclamation in separate event classes.
7. **Post-election review.** Recompute methodology against observed outcomes, document calibration errors, archive personal data according to policy, and publish an internal lessons record.

## 2026 distinction

October 2026 is not a presidential-election milestone. COMELEC currently lists a September 14, 2026 BARMM parliamentary election and a November 2, 2026 BSKE. The latter date and activity calendar are in [COMELEC Resolution 11191](https://www.comelec.gov.ph/index.html?r=2025BSKE%2FResolutions%2Fres11191), published in 2026. **Confidence:** high for the cited official calendar.

## COMELEC refresh checklist

Trigger this checklist whenever COMELEC publishes or amends a 2028 calendar or candidate record:

- archive the source document with publication, retrieval, and effective dates;
- compare dates and legal bases against the prior snapshot;
- update product copy, countdowns, and ingestion schedules;
- reconcile COC names/aliases to profiles with human review;
- record withdrawals, substitutions, nuisance/disqualification decisions, and appeals as separate dated events;
- update the demo’s freshness and coverage notice;
- run calendar-link, API-contract, and low-coverage tests;
- require analyst sign-off before changing authoritative status.

