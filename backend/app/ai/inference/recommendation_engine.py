"""recommendation_engine.py
============================
Clinical recommendation orchestration engine for the MediSys AI module.

This module is the **sole interface** between the FastAPI service layer and
the structured clinical knowledge base.  It exposes a single class,
:class:`RecommendationEngine`, whose :meth:`~RecommendationEngine.get_recommendation`
method accepts a predicted disease name and returns a :class:`RecommendationResult`
containing severity, specialist guidance, recommended tests, medications,
home care advice, warning signs, follow-up guidance, and a hospitalisation flag.

Design contract
----------------
* The knowledge base is loaded **lazily** on the first call to
  :meth:`~RecommendationEngine.get_recommendation`, not at import time.
  FastAPI workers that import this module pay no I/O cost unless a
  recommendation is actually requested.
* This engine **never** reads ``disease_recommendations.json`` directly,
  never calls :func:`json.load`, and never knows where the underlying data
  file lives on disk.  All knowledge access goes exclusively through the
  public functions exposed by :mod:`app.ai.knowledge.knowledge_base`
  (``load_knowledge()``, ``get_disease_data()``, ``list_known_diseases()``).
  This keeps the engine completely decoupled from the storage format and
  location of the clinical knowledge base.
* A disease name with **no entry** in the knowledge base never raises an
  exception. The engine returns a safe, generic fallback
  :class:`RecommendationResult` instead, so a gap in clinical content can
  never turn into a broken API response.

Usage as a script
------------------
Run from the ``backend/`` directory to verify the recommendation engine::

    python -m app.ai.recommendation.recommendation_engine
"""

import logging
import sys
from dataclasses import dataclass, field
from typing import Any

from app.ai.knowledge.knowledge_base import (
    get_disease_data,
    list_known_diseases,
    load_knowledge,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Values used to populate RecommendationResult when the predicted disease
# has no matching entry in the knowledge base. Kept as named constants
# (rather than inline literals) so the fallback contract is defined once
# and is trivially auditable.
_FALLBACK_SEVERITY: str = "Unknown"
_FALLBACK_SPECIALIST: str = "General Physician"

# Generic first-line investigations that a GP would order for any undiagnosed
# presentation — safe to recommend regardless of specific disease.
_FALLBACK_RECOMMENDED_TESTS: list[str] = [
    "Complete Blood Count (CBC)",
    "C-Reactive Protein (CRP)",
    "Erythrocyte Sedimentation Rate (ESR)",
    "Chest X-ray",
    "Pulse Oximetry",
    "Consult a General Physician for further evaluation",
]

# possible_medications is intentionally left empty for unknown diseases.
# Returning drug names without a confirmed diagnosis is clinically unsafe.
# The frontend should interpret an empty list + found_in_knowledge_base=False
# as "no medication guidance available until diagnosis is confirmed".
_FALLBACK_POSSIBLE_MEDICATIONS: list[str] = []

_FALLBACK_HOME_CARE: list[str] = [
    "Consult a qualified healthcare professional promptly.",
    "Do not self-medicate without medical advice.",
    "Rest and stay well hydrated.",
    "Monitor your symptoms and note any changes.",
]

# Universal warning signs that apply to any undiagnosed or deteriorating condition.
_FALLBACK_WARNING_SIGNS: list[str] = [
    "Difficulty breathing or shortness of breath",
    "Chest pain or pressure",
    "High fever not responding to medication",
    "Sudden confusion, drowsiness, or loss of consciousness",
    "Symptoms rapidly worsening",
]

_FALLBACK_FOLLOW_UP: str = (
    "See a General Physician as soon as possible for proper evaluation and diagnosis."
)
_FALLBACK_HOSPITALIZATION_REQUIRED: bool = False

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class RecommendationResult:
    """Container for the output of a single recommendation lookup.

    Args:
        disease: Name of the disease this recommendation applies to, as
            supplied by the caller (typically the top prediction from
            :class:`~app.ai.inference.predictor.DiseasePredictor`).
        severity: Clinical urgency level — one of ``"low"``, ``"moderate"``,
            ``"high"``, ``"critical"``, or ``"Unknown"`` if the disease was
            not found in the knowledge base.
        specialist: Recommended type of medical specialist to consult.
        recommended_tests: Ordered list of diagnostic investigations,
            first-line to confirmatory. Empty list if not documented.
        possible_medications: Drug classes / common agents associated with
            treatment. **Informational only — never a prescription.**
            Empty list if not documented.
        home_care: Practical self-care measures the patient can take.
        warning_signs: Symptoms or developments indicating the condition is
            worsening and warrants escalation to urgent care.
        follow_up: Guidance on expected follow-up cadence with a clinician.
        hospitalization_required: ``True`` if this condition may require
            hospitalisation or emergency care. ``False`` otherwise.
        found_in_knowledge_base: ``True`` if a real entry was found for
            this disease in the knowledge base, ``False`` if this result is
            the generic safe fallback. Callers can use this flag to decide
            whether to display a "limited information available" notice.
    """

    disease: str
    severity: str
    specialist: str
    recommended_tests: list[str] = field(default_factory=list)
    possible_medications: list[str] = field(default_factory=list)
    home_care: list[str] = field(default_factory=list)
    warning_signs: list[str] = field(default_factory=list)
    follow_up: str = ""
    hospitalization_required: bool = False
    found_in_knowledge_base: bool = True


# ---------------------------------------------------------------------------
# RecommendationEngine class
# ---------------------------------------------------------------------------


class RecommendationEngine:
    """Lazy-loading orchestration engine for clinical recommendations.

    The knowledge base is loaded via :func:`~app.ai.knowledge.knowledge_base.load_knowledge`
    the first time :meth:`get_recommendation` is called, and the resulting
    in-memory structure is cached as an instance attribute for all
    subsequent calls. This avoids blocking I/O at import time while keeping
    the loaded knowledge in memory across requests — the same pattern used
    by :class:`~app.ai.inference.predictor.DiseasePredictor` for ML artefacts.

    This class never imports :mod:`json`, never constructs file paths, and
    never knows whether the underlying knowledge base is backed by a JSON
    file, a database, or any other storage mechanism. All access is
    delegated exclusively to the public API of
    :mod:`app.ai.knowledge.knowledge_base`.

    Example:
        >>> engine = RecommendationEngine()
        >>> result = engine.get_recommendation("Diabetes")
        >>> print(result.specialist)
        'Endocrinologist / Diabetologist'
        >>> print(result.found_in_knowledge_base)
        True
    """

    def __init__(self) -> None:
        """Initialise the engine without loading the knowledge base.

        The knowledge base is loaded lazily on the first call to
        :meth:`get_recommendation`.
        """
        # Private attribute — set to None until _load_knowledge_base() is called.
        self._knowledge: Any = None

        # Flag that prevents repeated I/O on every request.
        self._loaded: bool = False

        logger.debug(
            "RecommendationEngine instantiated. "
            "Knowledge base will be loaded on first get_recommendation() call."
        )

    # ── Private: knowledge base loading ───────────────────────────────────────

    def _load_knowledge_base(self) -> None:
        """Load and cache the knowledge base via the public knowledge_base API.

        Delegates entirely to :func:`~app.ai.knowledge.knowledge_base.load_knowledge`.
        This engine has no awareness of file paths, JSON parsing, or storage
        format — that responsibility belongs solely to ``knowledge_base.py``.

        Raises:
            RuntimeError: If :func:`load_knowledge` fails (e.g. the knowledge
                base file is missing, corrupt, or fails schema validation).
                Wrapped with a clear message so the service layer can surface
                a meaningful HTTP 500. A broken knowledge base is a
                deployment-configuration problem and should fail loudly at
                load time rather than be silently tolerated per request.
        """
        logger.info("Loading clinical knowledge base …")

        try:
            self._knowledge = load_knowledge()
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load clinical knowledge base: {exc}. "
                "Check that the knowledge base data file exists and is valid."
            ) from exc

        self._loaded = True
        logger.info(
            "Knowledge base loaded and cached. %d disease(s) available. "
            "RecommendationEngine is ready.",
            len(list_known_diseases()),
        )

    # ── Private: fallback construction ────────────────────────────────────────

    def _build_fallback(self, disease: str) -> RecommendationResult:
        """Construct a safe, generic fallback result for an unknown disease.

        Used whenever the requested disease has no entry in the knowledge
        base. Guarantees the caller always receives a fully-populated,
        typed :class:`RecommendationResult` — never an exception — so a gap
        in clinical content can never break an API response.

        The fallback returns universal first-line investigations and home-care
        guidance that a General Physician would recommend for any undiagnosed
        presentation.  ``possible_medications`` is intentionally left empty:
        prescribing drug classes without a confirmed diagnosis is clinically
        unsafe, and the empty list combined with ``found_in_knowledge_base=False``
        is the correct signal for the frontend to display "no medication data
        available until diagnosis is confirmed".

        Args:
            disease: The disease name that was not found in the knowledge base.

        Returns:
            A :class:`RecommendationResult` populated with generic,
            universally applicable guidance and ``found_in_knowledge_base=False``.
        """
        logger.warning(
            "No knowledge base entry found for disease '%s'. "
            "Returning safe fallback recommendation.",
            disease,
        )

        return RecommendationResult(
            disease=disease,
            severity=_FALLBACK_SEVERITY,
            specialist=_FALLBACK_SPECIALIST,
            recommended_tests=list(_FALLBACK_RECOMMENDED_TESTS),
            possible_medications=list(_FALLBACK_POSSIBLE_MEDICATIONS),
            home_care=list(_FALLBACK_HOME_CARE),
            warning_signs=list(_FALLBACK_WARNING_SIGNS),
            follow_up=_FALLBACK_FOLLOW_UP,
            hospitalization_required=_FALLBACK_HOSPITALIZATION_REQUIRED,
            found_in_knowledge_base=False,
        )

    # ── Public: get_recommendation ────────────────────────────────────────────

    def get_recommendation(self, disease: str) -> RecommendationResult:
        """Return clinical recommendation guidance for a predicted disease.

        This is the primary public interface consumed by
        ``app/services/diagnosis_service.py``. It handles the complete
        recommendation pipeline: lazy knowledge base load → lookup → safe
        fallback (if needed) → result assembly.

        Args:
            disease: Disease name to look up, typically the top prediction
                returned by ``DiseasePredictor.predict().disease``.

        Returns:
            :class:`RecommendationResult` containing severity, specialist,
            recommended tests, possible medications, home care advice,
            warning signs, follow-up guidance, and hospitalisation flag.
            If ``disease`` has no entry in the knowledge base, a safe
            generic fallback is returned instead — this method never raises
            :exc:`ValueError` for an unrecognised disease name.

        Raises:
            RuntimeError: Propagated from :meth:`_load_knowledge_base` only
                if the knowledge base itself fails to load (missing or
                corrupt data file) — a system-level failure distinct from
                "disease not found", which is handled gracefully via fallback.

        Example:
            >>> engine = RecommendationEngine()
            >>> result = engine.get_recommendation("Heart Disease")
            >>> result.hospitalization_required
            True
            >>> result.specialist
            'Cardiologist'

            >>> result = engine.get_recommendation("Some Unlisted Condition")
            >>> result.found_in_knowledge_base
            False
            >>> result.specialist
            'General Physician'
        """
        logger.info(
            "Fallback tests constant = %s",
            _FALLBACK_RECOMMENDED_TESTS,
        )
        # ── Step 1: Lazy-load knowledge base ──────────────────────────────────
        # Skip if already loaded — the flag prevents repeated I/O across
        # multiple recommendation requests within the same process lifetime.
        if not self._loaded:
            self._load_knowledge_base()

        logger.debug("Looking up recommendation for disease: '%s'", disease)

        # ── Step 2: Look up the disease via the public knowledge_base API ─────
        # get_disease_data() is the ONLY way this engine ever touches
        # knowledge content — no direct dict access, no file I/O here.
        disease_data: dict[str, Any] | None = get_disease_data(disease)

        # ── Step 3: Handle missing entry with a safe fallback ─────────────────
        if disease_data is None:
            return self._build_fallback(disease)

        # ── Step 4: Build the result from the knowledge base entry ────────────
        result = RecommendationResult(
            disease=disease,
            severity=disease_data.get("severity", _FALLBACK_SEVERITY),
            specialist=disease_data.get("specialist", _FALLBACK_SPECIALIST),
            recommended_tests=list(disease_data.get("recommended_tests", [])),
            possible_medications=list(disease_data.get("possible_medications", [])),
            home_care=list(disease_data.get("home_care", [])),
            warning_signs=list(disease_data.get("warning_signs", [])),
            follow_up=disease_data.get("follow_up", _FALLBACK_FOLLOW_UP),
            hospitalization_required=bool(
                disease_data.get("hospitalization_required", False)
            ),
            found_in_knowledge_base=True,
        )

        logger.info(
            "Recommendation built for '%s' — severity=%s, specialist=%s, "
            "hospitalization_required=%s",
            disease,
            result.severity,
            result.specialist,
            result.hospitalization_required,
        )

        return result

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def is_loaded(self) -> bool:
        """Return True if the knowledge base has been loaded and cached.

        Returns:
            bool: True after the first successful call to
                :meth:`get_recommendation` or a direct call to
                :meth:`_load_knowledge_base`.
        """
        return self._loaded

    @property
    def n_known_diseases(self) -> int:
        """Return the number of diseases documented in the knowledge base.

        Returns:
            int: Number of diseases with a knowledge base entry, or 0 if
                not yet loaded.
        """
        if not self._loaded:
            return 0
        return len(list_known_diseases())


# ---------------------------------------------------------------------------
# Module-level singleton — imported by the service layer
# ---------------------------------------------------------------------------

# A single shared instance is created at module import time. Because the
# knowledge base is loaded lazily, this has no I/O cost until
# get_recommendation() is called. The service layer imports and uses this
# object directly:
#
#   from app.ai.recommendation.recommendation_engine import recommendation_engine
#   result = recommendation_engine.get_recommendation(predicted_disease)
#
recommendation_engine: RecommendationEngine = RecommendationEngine()


# ---------------------------------------------------------------------------
# Script entry point — manual verification
# ---------------------------------------------------------------------------


def main() -> None:
    """Run a quick smoke-test of the recommendation engine with sample diseases.

    Exercises the full recommendation pipeline (knowledge base loading,
    lookup, fallback handling) against a mix of known and deliberately
    unknown disease names. Output is logged at INFO level so it is visible
    when run from the command line.

    Exits with code 1 if any test case raises an unexpected exception.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    logger.info("═" * 56)
    logger.info("MediSys AI — Recommendation Engine Smoke Test")
    logger.info("═" * 56)

    engine = RecommendationEngine()

    # Test cases: disease names — a mix of diseases expected to exist in the
    # knowledge base and one deliberately unknown name to exercise the
    # fallback path.
    test_diseases: list[str] = [
        "Diabetes",
        "Heart Disease",
        "Common Cold",
        "Migraine",
        "Some Completely Unlisted Condition",  # exercises fallback path
    ]

    sep: str = "─" * 56
    all_passed: bool = True

    for disease in test_diseases:
        logger.info(sep)
        logger.info("Looking up recommendation for: '%s'", disease)
        try:
            result = engine.get_recommendation(disease)

            logger.info("Severity                 : %s", result.severity)
            logger.info("Specialist                : %s", result.specialist)
            logger.info("Recommended tests         : %s", result.recommended_tests)
            logger.info("Possible medications      : %s", result.possible_medications)
            logger.info("Home care                 : %s", result.home_care)
            logger.info("Warning signs             : %s", result.warning_signs)
            logger.info("Follow-up                 : %s", result.follow_up)
            logger.info(
                "Hospitalization required  : %s", result.hospitalization_required
            )
            logger.info(
                "Found in knowledge base   : %s", result.found_in_knowledge_base
            )

        except Exception as exc:
            logger.error("Recommendation lookup failed for '%s': %s", disease, exc)
            all_passed = False

    logger.info(sep)
    logger.info(
        "Smoke test complete — %s",
        "ALL LOOKUPS SUCCEEDED" if all_passed else "SOME LOOKUPS FAILED",
    )
    logger.info("Diseases documented in knowledge base: %d", engine.n_known_diseases)
    logger.info("═" * 56)

    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()