"""knowledge_base.py  (app/ai/knowledge/)
=========================================
Adapter layer between recommendation_engine.py and the canonical
Python knowledge base at app/ai/knowledge_base.py.

Why this file exists
---------------------
recommendation_engine.py was written against the finalized design doc's
API contract, which specifies three functions:

    load_knowledge()      → returns the full knowledge dict (for caching)
    get_disease_data()    → returns one disease entry or None
    list_known_diseases() → returns sorted list of disease names

The canonical knowledge base (app.ai.knowledge_base) exposes a different
but equivalent API:

    get_disease_info()    → equivalent to get_disease_data()
    list_diseases()       → equivalent to list_known_diseases()

This file is a thin compatibility adapter.  It imports from the canonical
module and re-exports the names the engine expects.  No business logic
lives here — it is pure API surface mapping.

This file also maps field names from the canonical DiseaseInfo schema
(``tests``, ``medications``) onto the JSON-schema field names the engine
reads (``recommended_tests``, ``possible_medications``, etc.), so the
engine always receives a consistent dict regardless of which backing
store is in use.

Extending in future
--------------------
If knowledge_base.py is later replaced with a database-backed implementation,
only the imports in this file change — recommendation_engine.py remains
completely unmodified.
"""

from typing import Any

from app.ai.knowledge_base import (
    DISEASE_KNOWLEDGE,
    get_disease_info,
    list_diseases,
)


# ---------------------------------------------------------------------------
# Field-name mapping
# ---------------------------------------------------------------------------
# The canonical DiseaseInfo schema (knowledge_base.py) uses:
#   tests, medications, home_care, emergency
#
# The recommendation engine (designed against the JSON schema) reads:
#   recommended_tests, possible_medications, home_care,
#   warning_signs, follow_up, hospitalization_required
#
# This mapping translates one into the other.

def _adapt(entry: dict[str, Any]) -> dict[str, Any]:
    """Convert a canonical DiseaseInfo dict into the engine's expected shape."""
    return {
        "severity":                entry.get("severity", "Unknown"),
        "specialist":              entry.get("specialist", "General Physician"),
        # canonical field: "tests" → engine field: "recommended_tests"
        "recommended_tests":       entry.get("tests", []),
        # canonical field: "medications" → engine field: "possible_medications"
        "possible_medications":    entry.get("medications", []),
        "home_care":               entry.get("home_care", []),
        # canonical schema has no "warning_signs" — return empty list
        "warning_signs":           entry.get("warning_signs", []),
        # canonical schema has no "follow_up" — derive from emergency flag
        "follow_up":               entry.get("follow_up", "Follow your doctor's advice."),
        # canonical field: "emergency" → engine field: "hospitalization_required"
        "hospitalization_required": entry.get("emergency", False),
    }


# ---------------------------------------------------------------------------
# Public API — matches the contract expected by recommendation_engine.py
# ---------------------------------------------------------------------------

def load_knowledge() -> dict[str, Any]:
    """Return the full knowledge dictionary, adapted to the engine's schema.

    Called once by RecommendationEngine._load_knowledge_base() on first use.
    The engine stores the result on self._knowledge but never reads it
    directly — all access goes through get_disease_data().

    Returns:
        dict mapping disease name → adapted entry dict.
    """
    return {name: _adapt(entry) for name, entry in DISEASE_KNOWLEDGE.items()}


def get_disease_data(disease_name: str) -> dict[str, Any] | None:
    """Return the adapted knowledge entry for disease_name, or None.

    Wraps get_disease_info() from the canonical knowledge base and adapts
    the field names to match the schema expected by recommendation_engine.py.

    Lookup is case-insensitive: the predictor outputs Title Case labels
    (e.g. ``"Heart Disease"``) while the knowledge base stores Title Case
    keys, but future model updates or dataset changes may produce different
    casing.  This function normalises both sides so a casing difference
    between the ML model output and the knowledge base key never causes a
    silent fallback.

    Args:
        disease_name: Disease name string as returned by the ML predictor.

    Returns:
        Adapted dict if found, None if disease_name has no entry in the
        knowledge base after case-insensitive matching.
    """
    # ── Primary lookup: exact match (fast, covers the normal case) ────────────
    entry = get_disease_info(disease_name)
    if entry is not None:
        return _adapt(entry)

    # ── Secondary lookup: case-insensitive scan ────────────────────────────────
    # Handles any casing mismatch between the ML label encoder output and the
    # knowledge base keys without requiring either side to change.
    disease_lower = disease_name.lower()
    for kb_name in DISEASE_KNOWLEDGE:
        if kb_name.lower() == disease_lower:
            entry = get_disease_info(kb_name)
            if entry is not None:
                return _adapt(entry)

    # Not found under any casing — caller handles via fallback
    return None


def list_known_diseases() -> list[str]:
    """Return a sorted list of all disease names in the knowledge base.

    Wraps list_diseases() from the canonical knowledge base.

    Returns:
        Sorted list of disease name strings.
    """
    return list_diseases()