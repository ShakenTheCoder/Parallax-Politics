"""Model router and pricing.

Centralized so model IDs and prices can be bumped without touching agents.
Prices are USD per 1M tokens — configured for NVIDIA NIM free endpoints.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass


class ModelTier(enum.StrEnum):
    cheap = "cheap"        # extraction, ranking, classification
    default = "default"    # synthesis, reasoning
    escalate = "escalate"  # Strategist hard cases only (gated by daily Opus cap)


@dataclass(frozen=True)
class ModelSpec:
    id: str
    tier: ModelTier
    input_per_mtok: float        # USD / 1M input tokens
    output_per_mtok: float       # USD / 1M output tokens
    cache_write_per_mtok: float  # Cache write multiplier (not applicable for free tier)
    cache_read_per_mtok: float   # Cache reads (not applicable for free tier)
    family: str                  # gemma
    context_window: int = 200_000
    fallback_id: str | None = None


# --- Registered models -------------------------------------------------------
# NVIDIA NIM free endpoint. This model is listed as available on NVIDIA's
# build.nvidia.com model page and uses the OpenAI-compatible NIM API.

GEMMA_4_31B = ModelSpec(
    id="meta/llama-3.3-70b-instruct",
    tier=ModelTier.default,
    input_per_mtok=0.0,  # Free tier
    output_per_mtok=0.0,  # Free tier
    cache_write_per_mtok=0.0,  # Not applicable for free tier
    cache_read_per_mtok=0.0,   # Not applicable for free tier
    family="llama",
)

# Use this verified NVIDIA free endpoint for all tiers.
_REGISTRY: dict[ModelTier, ModelSpec] = {
    ModelTier.cheap: GEMMA_4_31B,
    ModelTier.default: GEMMA_4_31B,
    ModelTier.escalate: GEMMA_4_31B,
}

_BY_ID: dict[str, ModelSpec] = {m.id: m for m in _REGISTRY.values()}


def pick_model(tier: ModelTier) -> ModelSpec:
    return _REGISTRY[tier]


def model_by_id(model_id: str) -> ModelSpec | None:
    return _BY_ID.get(model_id)


def estimate_cost_usd(
    model: ModelSpec,
    *,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> float:
    # NVIDIA free endpoint: all costs are $0
    # Cache operations are not applicable for the free tier
    return round(
        (input_tokens / 1_000_000) * model.input_per_mtok
        + (output_tokens / 1_000_000) * model.output_per_mtok
        + (cache_read_tokens / 1_000_000) * model.cache_read_per_mtok
        + (cache_write_tokens / 1_000_000) * model.cache_write_per_mtok,
        6,
    )
