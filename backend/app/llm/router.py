"""Model router and pricing.

Centralized so model IDs and prices can be bumped without touching agents.
Prices are USD per 1M tokens as configured for the NVIDIA NIM account.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class ModelTier(enum.StrEnum):
    cheap = "cheap"  # extraction, ranking, classification
    default = "default"  # synthesis, reasoning
    escalate = "escalate"  # Strategist hard cases only (gated by daily Opus cap)


@dataclass(frozen=True)
class ModelSpec:
    id: str
    tier: ModelTier
    input_per_mtok: float  # USD / 1M input tokens
    output_per_mtok: float  # USD / 1M output tokens
    cache_write_per_mtok: float
    cache_read_per_mtok: float
    family: str
    context_window: int = 200_000


# --- Registered models -------------------------------------------------------
# NVIDIA NIM endpoint. This model uses the OpenAI-compatible NIM API.

LLAMA_3_3_70B = ModelSpec(
    id="meta/llama-3.3-70b-instruct",
    tier=ModelTier.default,
    input_per_mtok=0.0,
    output_per_mtok=0.0,
    cache_write_per_mtok=0.0,
    cache_read_per_mtok=0.0,
    family="llama",
)

# Use this registered NVIDIA model for all tiers until tier-specific models are configured.
_REGISTRY: dict[ModelTier, ModelSpec] = {
    ModelTier.cheap: LLAMA_3_3_70B,
    ModelTier.default: LLAMA_3_3_70B,
    ModelTier.escalate: LLAMA_3_3_70B,
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
    return round(
        (input_tokens / 1_000_000) * model.input_per_mtok
        + (output_tokens / 1_000_000) * model.output_per_mtok
        + (cache_read_tokens / 1_000_000) * model.cache_read_per_mtok
        + (cache_write_tokens / 1_000_000) * model.cache_write_per_mtok,
        6,
    )
