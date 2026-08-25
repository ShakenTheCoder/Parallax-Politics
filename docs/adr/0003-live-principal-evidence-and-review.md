# ADR 0003: Live principal evidence, qualitative experiments, and review state

## Decision

Principal Brief and Analysis data are database projections over persisted,
provenance-bearing records. A missing input is `null`, `unavailable`, or an
explicit partial state; it is never replaced with a deterministic POC value.

Polls are a separate representative-evidence layer and require pollster,
field dates, sample, population, mode, uncertainty, exact question, geography,
results, source URL, and verification metadata. Polling never contributes to
momentum or rank.

Audience experiments are qualitative provider runs. Each run executes three
provider samples over every configured cohort and variant and stores consensus
and variance for six criteria. It must not return vote share, individual
predictions, targeting recommendations, or a best segment.

Generated briefs begin as `agent_draft`. Only a superadmin may approve or reject
one. Rejected rows remain immutable history and are visibly marked as rejected;
they are not approved recommendations.

## Consequences

The product can show less data during connector or provider failure, but every
displayed claim can be traced to a stored source or artifact. Schema migrations
are required before enabling poll review or Audience Lab execution in a new
environment.
