# Legal, ethics, and source policy

**Policy date:** 2026-08-24  
**Jurisdictional scope:** Philippines; platform/vendor terms also apply

This is a product policy, not legal advice. Philippine election and privacy counsel must review the system before production campaign use.

## Applicable baseline

The Data Privacy Act of 2012 and its implementing rules apply to personal-data processing. NPC Advisory 2021-03 requires transparency, legitimate purpose, proportionality, lawful basis, and safeguards for election-campaign processing. The NPC’s 2025 reminder specifically warns political organizations and candidates about these duties. NPC Advisory 2024-04 adds guidance for AI systems processing personal data.

Primary sources: [NPC election-campaign statement](https://privacy.gov.ph/on-the-collection-of-personal-information-for-election-campaign-purposes/), published 2025-04-07; [NPC election-campaign advisory PDF](https://privacy.gov.ph/wp-content/uploads/2021/11/Advisory_Election_Campaigning_03-Nov-21-FINAL.pdf), published 2021; [NPC advisories index](https://privacy.gov.ph/pips-and-pics/advisories-circulars/), including Advisory 2024-04. **Confidence:** high for the published NPC requirements; counsel must determine application to a concrete deployment.

## Prohibited uses

- voter dossiers, voter-level scoring, or joining political activity to identity/customer data;
- inferring ethnicity, religion, health, sexuality, political affiliation, wealth, or other sensitive traits;
- facial-emotion, biometric-affect, or physiological-response analysis;
- covert microtargeting or explaining a political message differently because of an inferred sensitive trait;
- private Messenger/group collection or use of unlawfully obtained datasets;
- automated publishing, autonomous campaign decisions, or generated statements represented as human-authored;
- synthetic grassroots activity, impersonation, coordinated inauthentic engagement, or fabricated testimonials;
- definitive bot/person attribution without an authoritative investigation;
- describing synthetic archetypes as polling, voter intent, persuasion lift, or individual prediction.

## Collection and source rights

Every connector must have a documented authorization/terms basis, permitted fields, retention window, rate limit, and deletion process. Robots compliance alone does not create a license. Store article links/excerpts rather than full text unless the license permits it. Preserve source attribution, publication time, capture time, rights classification, and takedown/suppression status.

Facebook/Instagram/TikTok owned analytics require explicit client authorization. Competitor-wide access is incomplete unless a licensed/authorized provider contract permits it. A vendor’s technical ability to collect data does not establish lawful or contractual permission.

## Survey disclosure

Poll cards must show pollster/sponsor where disclosed, field dates, population, sample, mode, exact question or faithful question summary, margin of error/credibility interval where applicable, geography, undecided/refused/none treatment, and source URL. A directional panel is labeled directional and cannot calibrate the electorate without a defensible design.

## AI and human review

Model output records provider/model version, Context Pack, time boundary, input evidence IDs, run time, confidence, and failure state. Consequential claims and all strategic next moves require an authorized analyst review record. Provider outage fails visibly or serves a labeled, previously completed frozen result. Models may propose classifications and summaries; they cannot establish candidacy, party membership, legal eligibility, identity, or source rights.

## Retention and access

- Apply least privilege by principal/client and analyst role.
- Keep immutable evidence/snapshot audit records for the approved research period; apply a documented deletion schedule to raw platform payloads and audio.
- Do not retain data merely because it was publicly accessible.
- Log export, review, status change, and deletion actions.
- Honor correction, takedown, contract, and legal-hold workflows without silently rewriting historical snapshots.

## Pre-production gate

Counsel review must cover campaign/election law, DPA lawful basis and notices, sensitive-information handling, vendor/platform terms, cross-border processing, survey disclosures, political-ad policies, automated-decision risks, retention, data-subject requests, incident response, and contracts with the client and each data/model provider.

