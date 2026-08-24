"""Authoritative research-watchlist membership shared by product surfaces.

Membership is mechanical: every figure below appeared in the same Pulse Asia
July 2026 hypothetical presidential long list. These are research-watchlist
figures, not filed candidates.
"""

from __future__ import annotations

from typing import Any

PULSE_ASIA_URL = (
    "https://pulseasia.ph/wp-content/uploads/2026/07/"
    "MR2-UB2026-2-MR-on-the-May-2028-Elections-Final.pdf"
)

WATCHLIST: tuple[dict[str, Any], ...] = (
    {
        "slug": "sara-duterte",
        "name": "Sara Duterte",
        "office": "Vice-President of the Philippines",
        "poll": 49.0,
        "strongest_channel": "Public video",
        "issue": "Executive leadership",
    },
    {
        "slug": "leni-robredo",
        "name": "Leni Robredo",
        "office": "Mayor of Naga City",
        "poll": 26.0,
        "strongest_channel": "Earned media",
        "issue": "Good governance",
    },
    {
        "slug": "raffy-tulfo",
        "name": "Raffy Tulfo",
        "office": "Senator of the Philippines",
        "poll": 14.0,
        "strongest_channel": "YouTube",
        "issue": "Public service",
    },
    {
        "slug": "vince-dizon",
        "name": "Vince Dizon",
        "office": "DPWH Secretary at poll publication",
        "poll": 1.0,
        "strongest_channel": "News",
        "issue": "Infrastructure delivery",
    },
    {
        "slug": "benjamin-magalong",
        "name": "Benjamin Magalong",
        "office": "Baguio City Mayor at poll publication",
        "poll": 1.0,
        "strongest_channel": "Local news",
        "issue": "Local governance",
    },
    {
        "slug": "nicolas-torre-iii",
        "name": "Nicolas Torre III",
        "office": "MMDA General Manager at poll publication",
        "poll": 0.1,
        "strongest_channel": "News",
        "issue": "Metropolitan operations",
    },
)
