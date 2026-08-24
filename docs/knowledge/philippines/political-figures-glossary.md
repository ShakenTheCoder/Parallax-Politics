# Political figures glossary

The Superadmin glossary is the national power-map registry for Parallax Politics.
It is deliberately separate from principal dossiers: a glossary profile can exist
for a public figure without granting that person a Parallax login.

## Initial roster policy

The seed covers the President, Vice President, the 24 members listed for the 20th
Congress Senate, and the existing 2028 watchlist figures. The seed stores only
source-backed roster facts and portrait provenance. Biography, policy positions,
electoral history, public interests, relationships, controversies, and social
accounts are refreshable evidence fields; unknown fields remain visible as gaps.

Primary roster references:

- [Office of the President officials directory](https://op-proper.gov.ph/transparency-seal-2/op-officials-directory/)
- [Senate of the Philippines, 20th Congress senators](https://legacy.senate.gov.ph/senators/sen20th.asp)
- [Existing Parallax watchlist evidence](./participants-and-competitors.md)

## Data contract

Each profile contains identity and office metadata, a structured dossier, public
social accounts, public relationships, portrait source and attribution, source
ledger, confidence, coverage gaps, and immutable refresh snapshots. Refresh output
must cite retrieved public URLs; the application rejects social account URLs that
were not present in the retrieved evidence pack. The product does not collect
private contact details, private family information, or non-public personal data.

Structured refreshes use Wikidata claims for identity metadata, Commons image claims
for portraits, and public-account identifiers for X, Facebook, Instagram, YouTube,
LinkedIn, and official websites. Current senators' account links are supplemented by
the official Senate 20th Congress directory. An account's `verification` field states
whether it came from Wikidata or an official institutional directory; office-level
accounts are identified as such and are not represented as personal accounts.

All source-backed facts are time-scoped by `accessed_at` and `last_verified_at`.
Superadmin refreshes append a snapshot instead of overwriting history.
