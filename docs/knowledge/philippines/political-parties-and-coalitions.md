# Political parties and coalitions

**Source date:** 2026-08-24  
**Retrieval date:** 2026-08-24  
**Scope:** affiliation policy and national-party catalog

## Evidence rule

A formal affiliation requires one of: an official party membership/leadership record, an election filing, an attributable party or member announcement, or an official biography that explicitly states membership. News coverage can locate a primary record but cannot establish affiliation on its own.

The following are separate relationship types and must never be collapsed into a `party` field:

- formal party membership or office;
- electoral coalition membership;
- one-election endorsement;
- legislative alliance or voting bloc;
- family/political network;
- event attendance or photo;
- media speculation.

Each relationship has effective dates and evidence. Conflicting sources remain visible.

## Initial national catalog

The POC source registry should monitor official publications from COMELEC and the parties themselves for PDP–Laban, Partido Federal ng Pilipinas, Lakas–CMD, Nacionalista Party, Nationalist People’s Coalition, National Unity Party, Liberal Party, Aksyon Demokratiko, Akbayan Citizens’ Action Party, Partido Demokratiko Sosyalista ng Pilipinas, Hugpong ng Pagbabago, and any COMELEC-accredited coalition relevant to the 2028 presidential ballot.

This list is a monitoring catalog, not a claim that each organization is currently in a particular coalition. Leadership and accreditation are time-sensitive and require refresh from the [COMELEC official site](https://www.comelec.gov.ph/) and first-party records.

## Six-person watchlist treatment

No party value is inferred from the Pulse Asia poll. Until primary evidence is loaded and reviewed, the POC can show “affiliation verification pending.” This is preferable to carrying forward a historic label that may no longer be current.

For each watchlist figure, retain an affiliation-history list with `organization`, `relationship_type`, `effective_from`, `effective_to`, `source_url`, and `confidence`. Appointed public office does not establish party membership. A coalition endorsement does not overwrite formal membership.

## Change workflow

1. Capture the official/first-party source and its publication date.
2. Confirm the named person and relationship type.
3. End-date the prior relationship only if the source supports a change.
4. Add the new relationship without deleting history.
5. Recompute competitor displays; do not recompute evidence-derived performance metrics from affiliation alone.
6. Require analyst review for ambiguous aliases or conflicting claims.

