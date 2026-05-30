"""Gap Taxonomy — structured classification of identity coverage gaps.

This module defines the standard taxonomy of coverage gaps that PIDAA can detect
and SCDRA can attempt to resolve. Each gap type includes severity classification,
auto-resolvability flags, and EXA search query templates.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GapType:
    """Definition of a coverage gap type."""
    id: str
    severity: str  # high/medium/low
    description: str
    affected_sections: tuple[str, ...]
    auto_resolvable: bool
    max_attempts: int = 3
    cost_budget_usd: float = 0.10
    query_templates: tuple[str, ...] = field(default_factory=tuple)

    def build_query(self, principal_name: str, **kwargs: Any) -> str:
        """Build a search query using the first available template."""
        if not self.query_templates:
            return f"{principal_name} {self.description}"
        template = self.query_templates[0]
        try:
            return template.format(name=principal_name, **kwargs)
        except KeyError:
            # Some template params missing - use simple replacement for name only
            # and remove remaining {placeholder} patterns
            result = template.replace("{name}", principal_name)
            import re
            result = re.sub(r"\{[^}]+\}", "", result)
            return result.strip()


# Standard Data Requirements Specification
# Maps each PIDAA section to required/important/optional fields
DATA_REQUIREMENTS: dict[str, dict[str, tuple[str, ...]]] = {
    "basics": {
        "mandatory": ("full_name", "born", "birthplace", "citizenship"),
        "important": ("aliases", "languages", "religion"),
        "optional": (),
    },
    "family": {
        "mandatory": ("spouse.name", "spouse.status", "parents"),
        "important": ("siblings", "children", "dynasty_links"),
        "optional": ("extended_family",),
    },
    "education": {
        "mandatory": ("degrees",),
        "important": ("degrees.*.year", "honors"),
        "optional": ("thesis_title", "dissertation"),
    },
    "career_timeline": {
        "mandatory": ("milestones",),
        "important": ("milestones.*.jurisdiction", "key_achievements"),
        "optional": (),
    },
    "current_position": {
        "mandatory": ("role", "jurisdiction"),
        "important": ("term_start", "term_end"),
        "optional": ("office_address",),
    },
    "party_history": {
        "mandatory": ("affiliations",),
        "important": ("affiliations.*.from", "affiliations.*.to"),
        "optional": ("switching_reason",),
    },
    "electoral_record": {
        "mandatory": ("races",),
        "important": ("races.*.votes", "races.*.rank", "races.*.opponent_names"),
        "optional": (),
    },
    "policy_stances": {
        "mandatory": ("wps_south_china_sea", "icc_drug_war"),
        "important": ("charter_change", "federalism", "ofw_policy"),
        "optional": ("confidential_funds", "social_services", "afp_pnp_expansion"),
    },
    "voice_signature": {
        "mandatory": ("languages_used", "tone"),
        "important": ("signature_phrases", "preferred_formats"),
        "optional": ("notes",),
    },
    "controversies": {
        "mandatory": ("items",),
        "important": ("items.*.severity", "items.*.status", "items.*.summary"),
        "optional": ("items.*.legal_outcome",),
    },
    "network": {
        "mandatory": ("allies", "rivals"),
        "important": ("key_staff",),
        "optional": ("political_mentors",),
    },
}


# Gap Taxonomy Definitions
# Maps gap_type identifiers to GapType definitions with query templates
GAP_TAXONOMY: dict[str, GapType] = {
    # --- High severity gaps ---
    "birth_record_missing": GapType(
        id="birth_record_missing",
        severity="high",
        description="No PSA/Comelec birth verification available",
        affected_sections=("basics",),
        auto_resolvable=True,
        max_attempts=3,
        cost_budget_usd=0.10,
        query_templates=(
            "{name} Philippines birth certificate PSA",
            "{name} born {birthplace} birthdate",
            "{name} Philippines birth record verification",
        ),
    ),
    "education_unverified": GapType(
        id="education_unverified",
        severity="high",
        description="No official educational credentials or degree records found",
        affected_sections=("education",),
        auto_resolvable=True,
        max_attempts=3,
        cost_budget_usd=0.10,
        query_templates=(
            "{name} {institution} degree graduation",
            "{name} education background university",
            "{name} alma mater academic credentials",
        ),
    ),
    "controversy_legal_status_unknown": GapType(
        id="controversy_legal_status_unknown",
        severity="high",
        description="Controversy resolution status or legal outcome unclear",
        affected_sections=("controversies",),
        auto_resolvable=True,
        max_attempts=3,
        cost_budget_usd=0.10,
        query_templates=(
            "{name} {controversy_label} case status legal outcome",
            "{name} {controversy_label} court decision resolution",
            "{name} {controversy_label} dismissed convicted",
        ),
    ),
    # --- Medium severity gaps ---
    "religion_conversion_unconfirmed": GapType(
        id="religion_conversion_unconfirmed",
        severity="medium",
        description="Exact date and circumstances of religious conversion not confirmed",
        affected_sections=("basics",),
        auto_resolvable=True,
        max_attempts=2,
        cost_budget_usd=0.08,
        query_templates=(
            "{name} converted religion date circumstances",
            "{name} Islam Christianity conversion story",
            "{name} religious conversion interview",
        ),
    ),
    "mother_biography_missing": GapType(
        id="mother_biography_missing",
        severity="medium",
        description="Mother's full biographical details absent from source pack",
        affected_sections=("family",),
        auto_resolvable=True,
        max_attempts=2,
        cost_budget_usd=0.08,
        query_templates=(
            "{name} mother biography family background",
            "{name} parents mother name occupation",
            "{name} family history mother",
        ),
    ),
    "term_dates_incomplete": GapType(
        id="term_dates_incomplete",
        severity="medium",
        description="Term start/end dates not confirmed for current position",
        affected_sections=("current_position",),
        auto_resolvable=True,
        max_attempts=2,
        cost_budget_usd=0.08,
        query_templates=(
            "{name} term start date oath office {role}",
            "{name} {role} elected sworn in date",
            "{name} term length expiration {role}",
        ),
    ),
    "policy_direct_quote_missing": GapType(
        id="policy_direct_quote_missing",
        severity="medium",
        description="No direct statement or quote found for key policy position",
        affected_sections=("policy_stances",),
        auto_resolvable=True,
        max_attempts=2,
        cost_budget_usd=0.08,
        query_templates=(
            "{name} {policy_topic} statement quote position",
            "{name} {policy_topic} interview speech transcript",
            "{name} stance {policy_topic} direct quote",
        ),
    ),
    # --- Low severity gaps ---
    "family_children_incomplete": GapType(
        id="family_children_incomplete",
        severity="low",
        description="Full list of children and their mothers not comprehensively documented",
        affected_sections=("family",),
        auto_resolvable=True,
        max_attempts=2,
        cost_budget_usd=0.05,
        query_templates=(
            "{name} children family sons daughters",
            "{name} wife children family photo",
            "{name} family personal life children",
        ),
    ),
    "siblings_details_missing": GapType(
        id="siblings_details_missing",
        severity="low",
        description="Siblings' full names and political roles not confirmed",
        affected_sections=("family",),
        auto_resolvable=True,
        max_attempts=2,
        cost_budget_usd=0.05,
        query_templates=(
            "{name} siblings brother sister family",
            "{name} family siblings names",
            "{name} political dynasty relatives",
        ),
    ),
    "electoral_votes_missing": GapType(
        id="electoral_votes_missing",
        severity="low",
        description="Vote counts not available in source pack for electoral races",
        affected_sections=("electoral_record",),
        auto_resolvable=True,
        max_attempts=2,
        cost_budget_usd=0.05,
        query_templates=(
            "{name} {year} election votes count Comelec",
            "{name} {year} {office} election results votes",
            "{name} {year} election vote total tally",
        ),
    ),
    "network_strength_unverified": GapType(
        id="network_strength_unverified",
        severity="low",
        description="Ally/rival relationship strength inferred but not confirmed",
        affected_sections=("network",),
        auto_resolvable=True,
        max_attempts=2,
        cost_budget_usd=0.05,
        query_templates=(
            "{name} {ally_name} alliance relationship",
            "{name} {rival_name} conflict rivalry",
            "{name} political allies supporters",
        ),
    ),
    "party_switch_date_unknown": GapType(
        id="party_switch_date_unknown",
        severity="low",
        description="Party affiliation change date unclear or approximate only",
        affected_sections=("party_history",),
        auto_resolvable=True,
        max_attempts=2,
        cost_budget_usd=0.05,
        query_templates=(
            "{name} switched party {old_party} {new_party} date",
            "{name} party affiliation change when",
            "{name} left {old_party} joined {new_party}",
        ),
    ),
}


def get_gap_type(gap_type_id: str) -> GapType | None:
    """Retrieve a GapType definition by its ID."""
    return GAP_TAXONOMY.get(gap_type_id)


def list_gap_types(severity: str | None = None, auto_resolvable: bool | None = None) -> list[GapType]:
    """List all gap types, optionally filtered by severity or auto_resolvable flag."""
    gaps = list(GAP_TAXONOMY.values())
    if severity:
        gaps = [g for g in gaps if g.severity == severity]
    if auto_resolvable is not None:
        gaps = [g for g in gaps if g.auto_resolvable == auto_resolvable]
    return gaps


def calculate_data_completeness(identity_sections: dict[str, Any]) -> float:
    """Calculate data completeness score (0.0-1.0) based on required fields present.

    Args:
        identity_sections: Dict with all 11 PIDAA section data

    Returns:
        Float between 0.0 and 1.0 representing completeness percentage
    """
    if not identity_sections:
        return 0.0

    total_required = 0
    total_present = 0

    for section, requirements in DATA_REQUIREMENTS.items():
        section_data = identity_sections.get(section, {})

        # Check mandatory fields
        for field in requirements["mandatory"]:
            total_required += 1
            if _field_present(section_data, field):
                total_present += 1

        # Check important fields (weighted 0.5)
        for field in requirements["important"]:
            total_required += 0.5
            if _field_present(section_data, field):
                total_present += 0.5

    if total_required == 0:
        return 0.0

    return round(total_present / total_required, 2)


def _field_present(data: dict[str, Any], field_path: str) -> bool:
    """Check if a field is present and non-empty in nested data.

    Supports simple field names and wildcard paths like "degrees.*.year".
    """
    if not data:
        return False

    # Handle wildcard paths
    if ".*" in field_path:
        parts = field_path.split(".*")
        base_field = parts[0]
        remainder = parts[1].lstrip(".") if len(parts) > 1 else ""

        base_value = data.get(base_field)
        if not isinstance(base_value, list) or not base_value:
            return False

        # Check that at least one item in the list has the remainder field
        if not remainder:
            return True

        for item in base_value:
            if _field_present(item, remainder):
                return True
        return False

    # Simple field path
    parts = field_path.split(".")
    current = data

    for part in parts:
        if not isinstance(current, dict):
            return False
        if part not in current:
            return False
        current = current[part]

    # Check for non-empty value
    if current is None:
        return False
    if isinstance(current, (list, dict)) and not current:
        return False
    if isinstance(current, str) and not current.strip():
        return False

    return True


def detect_gaps_from_pidaa_output(identity_sections: dict[str, Any]) -> list[dict[str, Any]]:
    """Detect coverage gaps from PIDAA output based on missing required fields.

    Returns a list of CoverageGap-compatible dicts.
    """
    gaps: list[dict[str, Any]] = []

    # Check basics section
    basics = identity_sections.get("basics", {})
    if not basics.get("born"):
        gaps.append({
            "gap_type": "birth_record_missing",
            "severity": "high",
            "description": GAP_TAXONOMY["birth_record_missing"].description,
            "affected_fields": ["basics.born"],
            "auto_resolvable": True,
            "status": "pending",
        })

    # Check education section
    education = identity_sections.get("education", {})
    degrees = education.get("degrees", [])
    if not degrees or all(not d.get("institution") for d in degrees):
        gaps.append({
            "gap_type": "education_unverified",
            "severity": "high",
            "description": GAP_TAXONOMY["education_unverified"].description,
            "affected_fields": ["education.degrees"],
            "auto_resolvable": True,
            "status": "pending",
        })

    # Check family section
    family = identity_sections.get("family", {})
    children = family.get("children", [])
    if children and any(not c.get("name") for c in children):
        gaps.append({
            "gap_type": "family_children_incomplete",
            "severity": "low",
            "description": GAP_TAXONOMY["family_children_incomplete"].description,
            "affected_fields": ["family.children"],
            "auto_resolvable": True,
            "status": "pending",
        })

    if not family.get("siblings"):
        gaps.append({
            "gap_type": "siblings_details_missing",
            "severity": "low",
            "description": GAP_TAXONOMY["siblings_details_missing"].description,
            "affected_fields": ["family.siblings"],
            "auto_resolvable": True,
            "status": "pending",
        })

    if not family.get("parents") or len(family.get("parents", [])) < 2:
        gaps.append({
            "gap_type": "mother_biography_missing",
            "severity": "medium",
            "description": GAP_TAXONOMY["mother_biography_missing"].description,
            "affected_fields": ["family.parents"],
            "auto_resolvable": True,
            "status": "pending",
        })

    # Check current position section
    current = identity_sections.get("current_position", {})
    if current.get("role") and not current.get("term_start"):
        gaps.append({
            "gap_type": "term_dates_incomplete",
            "severity": "medium",
            "description": GAP_TAXONOMY["term_dates_incomplete"].description,
            "affected_fields": ["current_position.term_start"],
            "auto_resolvable": True,
            "status": "pending",
        })

    # Check electoral record section
    electoral = identity_sections.get("electoral_record", {})
    races = electoral.get("races", [])
    if races and any(r.get("won") and not r.get("votes") for r in races):
        gaps.append({
            "gap_type": "electoral_votes_missing",
            "severity": "low",
            "description": GAP_TAXONOMY["electoral_votes_missing"].description,
            "affected_fields": ["electoral_record.races.*.votes"],
            "auto_resolvable": True,
            "status": "pending",
        })

    # Check policy stances section
    policy = identity_sections.get("policy_stances", {})
    mandatory_policies = DATA_REQUIREMENTS["policy_stances"]["mandatory"]
    for policy_key in mandatory_policies:
        policy_data = policy.get(policy_key, {})
        if not policy_data.get("value"):
            gaps.append({
                "gap_type": "policy_direct_quote_missing",
                "severity": "medium",
                "description": f"No direct statement found for {policy_key}",
                "affected_fields": [f"policy_stances.{policy_key}"],
                "auto_resolvable": True,
                "status": "pending",
            })

    # Check controversies section
    controversies = identity_sections.get("controversies", {})
    items = controversies.get("items", [])
    for item in items:
        if item.get("severity", 0) > 0.5 and item.get("status") not in ("resolved", "dismissed"):
            if not item.get("status"):
                gaps.append({
                    "gap_type": "controversy_legal_status_unknown",
                    "severity": "high",
                    "description": f"Legal status unclear for controversy: {item.get('label', 'Unknown')}",
                    "affected_fields": ["controversies.items.*.status"],
                    "auto_resolvable": True,
                    "status": "pending",
                })

    # Check network section
    network = identity_sections.get("network", {})
    allies = network.get("allies", [])
    rivals = network.get("rivals", [])
    if allies and any(not a.get("strength") for a in allies):
        gaps.append({
            "gap_type": "network_strength_unverified",
            "severity": "low",
            "description": GAP_TAXONOMY["network_strength_unverified"].description,
            "affected_fields": ["network.allies.*.strength"],
            "auto_resolvable": True,
            "status": "pending",
        })

    # Check party history section
    party = identity_sections.get("party_history", {})
    affiliations = party.get("affiliations", [])
    if len(affiliations) > 1:
        # Has party switches - check if dates are missing
        for aff in affiliations:
            if not aff.get("from") and not aff.get("to"):
                gaps.append({
                    "gap_type": "party_switch_date_unknown",
                    "severity": "low",
                    "description": GAP_TAXONOMY["party_switch_date_unknown"].description,
                    "affected_fields": ["party_history.affiliations.*.from", "party_history.affiliations.*.to"],
                    "auto_resolvable": True,
                    "status": "pending",
                })
                break  # Only add once

    # Check religion conversion
    religion = basics.get("religion", "")
    if religion and any(word in religion.lower() for word in ["convert", "converted", "formerly"]):
        if not basics.get("conversion_date") and "conversion" not in basics:
            gaps.append({
                "gap_type": "religion_conversion_unconfirmed",
                "severity": "medium",
                "description": GAP_TAXONOMY["religion_conversion_unconfirmed"].description,
                "affected_fields": ["basics.religion"],
                "auto_resolvable": True,
                "status": "pending",
            })

    return gaps
