# Participants and competitors

**Source date:** 2026-08-24  
**Retrieval date:** 2026-08-24  
**Scope:** initial national research watchlist

## Authoritative watchlist rule

The initial watchlist is exactly the six people in Pulse Asia Research’s July 22, 2026 release about its June 28–July 3 and July 6 nationwide face-to-face survey. The representative sample was 2,400 adults and the national error margin was ±2 percentage points at 95% confidence. The survey question was explicitly hypothetical. Source: [Pulse Asia July 2026 report](https://pulseasia.ph/wp-content/uploads/2026/07/MR2-UB2026-2-MR-on-the-May-2028-Elections-Final.pdf), published 2026-07-22. **Geography:** Philippines. **Confidence:** high for poll inclusion; no inference of candidacy.

| Profile / aliases | Office as of source period | Poll inclusion | Declared intention | Evidence gaps | Current watch status |
|---|---|---:|---|---|---|
| Sara Zimmerman Duterte; Sara Duterte; Inday Sara | Vice-President of the Philippines | 49% | Public reporting records a 2028 intention; retain the declaration source separately from filing status | Official account and formal current affiliation need periodic re-verification | `officeholder`, `polled_hypothetical`; never `filed_candidate` before COC evidence |
| Maria Leonor Gerona Robredo; Leni Robredo | Mayor of Naga City | 26% | Public statements reported in 2026 rule out a national run; a status-history event must retain the dated source | Re-verify intention after any attributable statement | `officeholder`, `polled_hypothetical` |
| Rafael Teshiba Tulfo; Raffy Tulfo; Idol Raffy | Senator of the Philippines | 14% | No filing exists for 2028 | Official channel inventory and any attributable declaration | `officeholder`, `polled_hypothetical` |
| Vivencio Bringas Dizon; Vince Dizon | Secretary of Public Works and Highways in the poll release | 1% | No filing exists for 2028 | Current office, formal affiliation, and official channels require re-check on every refresh | `officeholder`, `polled_hypothetical` |
| Benjamin Banez Magalong; Benjie Magalong | Mayor of Baguio City in the poll release | 1% | No filing exists for 2028 | Reconcile reported retirement/non-run comments to a primary transcript | `officeholder`, `polled_hypothetical` |
| Nicolas Deloso Torre III; Nic Torre; Nicolas Torre III | MMDA General Manager in the poll release | 0.1% | No filing exists for 2028 | Official biography, accounts, affiliation, and current-office check | `officeholder`, `polled_hypothetical` |

Office corroboration currently available from [Naga City Mayor’s Office](https://www2.naga.gov.ph/office-service/city-mayors-office/) and the [Senate biography of Raffy Tulfo](https://legacy.senate.gov.ph/senators/sen_bio/tulfo_raffy_bio.asp). For the other profiles, the Pulse Asia report supports the office label **at publication time**, not indefinitely. All office claims are therefore effective-dated.

## Profile evidence contract

Every profile stores stable aliases, official biography URL, first-party public-account URLs, and an append-only status history. A status event contains `status`, `effective_from`, optional `effective_to`, `source_url`, source publication date, capture time, and reviewer. Unknown data stays unknown.

Allowed status values:

- `officeholder`
- `polled_hypothetical`
- `declared_aspirant`
- `filed_candidate`
- `withdrawn`
- `disqualified`

The product label is “watchlist figure” until an authoritative filing or declaration supports something more specific.

## Mechanical competitor definition

For this product, competitors are figures who appear in the same named hypothetical-race question or, later, the same official ballot contest. The relationship must point to a profile and evidence record with effective dates. Free-form LLM rival invention is not authoritative and must not write competitor records.

The six initial figures are mutual competitors only within the Pulse Asia long-list context. That relationship must not be generalized to another office, election, or period.

### Brief identity-resolution invariant

The Brief derives membership from the versioned race watchlist for every signed-in principal; it does not trust account-specific, name-only competitor rows to define the set. Each displayed name is resolved by exact canonical name or reviewed alias to the Superadmin political-figure glossary. Current role and portrait come from that resolved glossary record, including alias pairs such as Benjamin/Benjie Magalong and Nicolas/Nic Torre. The signed-in figure replaces their watchlist row and is marked `is_principal`, so a person is never shown as their own competitor. Missing glossary matches remain visibly unverified rather than triggering fuzzy identity substitution.

## Poll record

- Pollster: Pulse Asia Research, Inc.
- Publication: July 22, 2026
- Field dates: June 28–July 3 and July 6, 2026
- Sample: 2,400 representative adults aged 18+
- Mode: face-to-face interviews
- National margin of error: ±2 percentage points at 95% confidence
- Question: choice for President if the May 2028 election were held during the survey period and the listed people were candidates
- Result order: Sara Duterte 49%, Leni Robredo 26%, Raffy Tulfo 14%, Vince Dizon 1%, Benjamin Magalong 1%, Nicolas Torre III 0.1%
- Layer: representative polling, excluded from Campaign Momentum
