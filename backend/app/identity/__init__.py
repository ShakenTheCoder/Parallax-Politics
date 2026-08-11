"""Identity module — data requirements and gap taxonomy for principal identities."""

from app.identity.gap_taxonomy import (
    DATA_REQUIREMENTS,
    GAP_TAXONOMY,
    GapType,
    calculate_data_completeness,
    detect_gaps_from_pidaa_output,
    get_gap_type,
    list_gap_types,
)

__all__ = [
    "DATA_REQUIREMENTS",
    "GAP_TAXONOMY",
    "GapType",
    "calculate_data_completeness",
    "detect_gaps_from_pidaa_output",
    "get_gap_type",
    "list_gap_types",
]
