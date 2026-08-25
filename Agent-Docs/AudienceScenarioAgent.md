# Audience Scenario Agent contract

The Audience Scenario Agent evaluates message variants qualitatively across all
configured cohorts. It runs three independent provider samples per request.

Each evaluation contains only these six 1–5 criteria: clarity, relevance,
credibility, objection risk, recall, and sharing inclination. The persisted
artifact contains all sample evaluations plus consensus and variance.

The agent must not produce vote share, individual voter predictions, targeting
recommendations, or a best segment. Provider failure is a failed/unavailable
run and must never be replaced by deterministic scores.
