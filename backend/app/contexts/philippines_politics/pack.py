"""Metadata for the 'philippines_politics' context pack."""

PACK_META = {
    "id": "philippines_politics",
    "label": "Philippine Political Intelligence",
    "principal_archetype": "Philippine politician / public official",

    "emotions": (
        "anger", "ridicule", "disappointment", "fatigue",
        "fear", "betrayal", "trust", "pride",
    ),
    "dimensions": (
        "competence", "empathy", "integrity",
        "decisiveness", "maka_masa_vs_elitist", "crisis_command",
    ),

    "source_domain_hints": (
        "gov.ph", "senate.gov.ph", "congress.gov.ph", "comelec.gov.ph",
        "ovp.gov.ph", "psa.gov.ph", "pna.gov.ph",
        "rappler.com", "inquirer.net", "gmanetwork.com", "philstar.com",
        "mb.com.ph", "bworldonline.com", "abs-cbn.com", "tv5.com.ph",
        "businessmirror.com.ph", "sunstar.com.ph", "manilatimes.net",
    ),

    "cohort_template": (
        "NCR media class",
        "Solid North (Ilocos / Pangasinan)",
        "Central Luzon",
        "CALABARZON",
        "Visayas swing (Cebuano-speaking)",
        "Mindanao Duterte base (Davao / SOCCSKSARGEN)",
        "BARMM bloc (Muslim minority)",
        "OFW diaspora",
        "Gen Z TikTok-native (18–24)",
        "Catholic majority",
        "INC bloc",
    ),

    "intake_prompt_template": (
        "Build a comprehensive intelligence dossier for the Philippine political principal: {name}. "
        "Gather all publicly available information about their background, career, current political position, "
        "party affiliation, key allies and rivals, public stances on major issues (WPS, charter change, "
        "ICC, confidential funds, social services, federalism, AFP/PNP), recent media footprint, "
        "and known vulnerabilities. This is the principal's intake run — no prior profile exists; "
        "build from scratch using name search plus the Philippine political context."
    ),
}
