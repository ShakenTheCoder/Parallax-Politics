# Philippines 2028 election knowledge bundle

**Source date:** 2026-08-24  
**Retrieval date:** 2026-08-24  
**Geographic scope:** Philippines, with regional detail where a cited source supports it

This bundle defines the evidence and language used by the Parallax Politics proof of concept (POC). It is a research watchlist and analytical system, not a candidate registry, voter file, or forecast of election results.

## Election distinction

The next regular Philippine presidential election is expected on **May 8, 2028**. Republic Act No. 7166 synchronizes the presidential election every six years on the second Monday of May, and the Constitution establishes a six-year presidential term. The precise 2028 calendar remains subject to a future COMELEC resolution. October 2026 is **not** a presidential-election month. The nearby official events currently documented are the September 14, 2026 BARMM parliamentary election and the November 2, 2026 Barangay and Sangguniang Kabataan Elections (BSKE).

Sources: [1987 Constitution](https://lawphil.net/consti/cons1987.html), [RA 7166](https://lawphil.net/statutes/repacts/ra1991/ra_7166_1991.html), [COMELEC Resolution 11191](https://www.comelec.gov.ph/index.html?r=2025BSKE%2FResolutions%2Fres11191). **Publication dates:** 1987, 1991, and 2026. **Confidence:** high for the statutory cycle and published 2026 BSKE date; medium for the exact 2028 date until COMELEC publishes its calendar.

## Required terminology

- **Watchlist figure:** a person included for research because an identified poll placed them in the same hypothetical race. This does not imply candidacy.
- **`polled_hypothetical`:** the default watch status for all six initial figures. It may coexist with `officeholder` in status history.
- **Declared aspirant:** a figure whose intention is supported by a dated, attributable declaration. It is still not the same as a filed candidacy.
- **Filed candidate:** a person listed in official COMELEC certificate-of-candidacy records for the relevant contest.
- **Signal:** a time-stamped public observation with source and rights metadata.
- **Evidence layer:** one of observed public performance, authorized owned analytics, representative polling, or synthetic simulation. Layers must never be blended without labels.
- **Synthetic archetype:** an explicitly artificial summary of an aggregate cohort. It is not an individual, poll respondent, voter-intent estimate, or target segment.

## Claim contract

Every material claim stored by the product or added to this bundle must include:

1. `source_url` pointing to the most authoritative available record;
2. publication or effective date;
3. retrieval date;
4. geographic scope;
5. confidence (`high`, `medium`, or `low`) and a short reason;
6. whether the claim is observed, reported, calculated, or inferred.

No source means no authoritative claim. Conflicts remain visible and are not silently resolved by a model.

## Source hierarchy

1. Constitution, statute, COMELEC resolution or official election record.
2. PSA, NPC, Senate, local-government, department, or other primary public record.
3. Pollster release containing field dates, sample, question wording, and uncertainty.
4. Verified first-party public account or attributable appearance transcript.
5. Licensed news/data feed and established newsroom reporting.
6. Public web or platform snapshot with clear capture time and rights limits.
7. Analyst inference, always labeled and never used to establish formal status or affiliation.

## Update cadence

- COMELEC calendar, filings, withdrawals, and disqualifications: daily during filing/campaign periods; weekly otherwise.
- Offices, party affiliations, official accounts, and declared intentions: weekly and after a material event.
- Polls and public appearances: on publication, with same-day source checking.
- Demographics: when PSA or COMELEC releases a relevant table; review quarterly.
- Vendor prices and platform access terms: monthly and before procurement.
- Methodology: versioned; changes require recomputation, not silent restatement.

## Index

- [Demographics and electorate](demographics-and-electorate.md)
- [2028 election roadmap](2028-election-roadmap.md)
- [Participants and competitors](participants-and-competitors.md)
- [Political parties and coalitions](political-parties-and-coalitions.md)
- [Media and data source catalog](media-and-data-source-catalog.md)
- [Free data acquisition for the Brief](free-data-acquisition-for-brief.md)
- [Metrics and ranking methodology](metrics-and-ranking-methodology.md)
- [Product blueprint and POC roadmap](product-blueprint-and-poc-roadmap.md)
- [Third-party services and costs](third-party-services-and-costs.md)
- [Legal, ethics, and source policy](legal-ethics-and-source-policy.md)
