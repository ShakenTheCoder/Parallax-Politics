"""Canonical fleet registry exposed to operators and orchestration."""

from app.schemas.intelligence import AgentDefinition

AGENT_FLEET = [
    AgentDefinition(
        id="acquisition-planner",
        name="Acquisition Planner",
        role="Plans authorized source coverage and schedules.",
        stage="collection",
    ),
    AgentDefinition(
        id="entity-resolution",
        name="Entity Resolution Agent",
        role="Resolves candidate aliases, organizations, pages, and coalitions.",
        stage="normalization",
    ),
    AgentDefinition(
        id="evidence-veracity",
        name="Evidence and Veracity Agent",
        role="Checks provenance, corroboration, contradictions, and source quality.",
        stage="verification",
    ),
    AgentDefinition(
        id="language-normalization",
        name="Translation and Language Agent",
        role="Normalizes English, Filipino, and code-switched evidence while retaining originals.",
        stage="normalization",
    ),
    AgentDefinition(
        id="narrative-intelligence",
        name="Narrative Intelligence Agent",
        role="Tracks narrative origin, velocity, mutation, reach, and candidate association.",
        stage="analysis",
    ),
    AgentDefinition(
        id="presence-analytics",
        name="Presence Analytics Agent",
        role="Measures visibility, engagement quality, issue ownership, and momentum.",
        stage="analysis",
    ),
    AgentDefinition(
        id="demographic-intelligence",
        name="Demographic Intelligence Agent",
        role="Builds privacy-safe aggregate cohort context from representative evidence.",
        stage="analysis",
    ),
    AgentDefinition(
        id="competitor-intelligence",
        name="Competitor Intelligence Agent",
        role="Compares positioning, coalitions, issue ownership, and audience overlap.",
        stage="analysis",
    ),
    AgentDefinition(
        id="network-intelligence",
        name="Network Intelligence Agent",
        role="Maps public media, endorsement, organizational, and influence networks.",
        stage="analysis",
    ),
    AgentDefinition(
        id="poll-calibration",
        name="Poll Calibration Agent",
        role="Calibrates online indicators against representative polling and consented panels.",
        stage="calibration",
    ),
    AgentDefinition(
        id="population-response",
        name="Population Response Agent",
        role="Produces cohort-level response ranges with explicit uncertainty.",
        stage="forecasting",
    ),
    AgentDefinition(
        id="scenario-simulation",
        name="Scenario Simulation Agent",
        role="Compares proposed public actions against a frozen evidence context.",
        stage="forecasting",
    ),
    AgentDefinition(
        id="strategy",
        name="Strategy Agent",
        role="Drafts evidence-backed communication and issue-prioritization options.",
        stage="strategy",
    ),
    AgentDefinition(
        id="adversarial-critic",
        name="Adversarial Critic Agent",
        role="Challenges causality, bias, confounders, and overconfidence.",
        stage="review",
    ),
    AgentDefinition(
        id="compliance",
        name="Compliance Agent",
        role="Blocks prohibited collection, sparse cohorts, and unsupported recommendations.",
        stage="review",
    ),
    AgentDefinition(
        id="executive-brief",
        name="Executive Brief Agent",
        role="Synthesizes approved intelligence for campaign leadership.",
        stage="publication",
        verdict_authority=False,
    ),
]
