"""predictor.py
===============
Runtime inference engine for the MediSys disease-prediction model.

This module is the **sole interface** between the FastAPI service layer and
the trained scikit-learn artefacts.  It exposes a single class,
:class:`DiseasePredictor`, whose :meth:`~DiseasePredictor.predict` method
accepts a list of symptom strings and returns a :class:`PredictionResult`
containing the top-3 most probable diseases with confidence percentages.

Design contract
---------------
* Artefacts are loaded **lazily** on the first call to
  :meth:`~DiseasePredictor.predict`, not at import time.  FastAPI workers
  that import this module pay no I/O cost unless a prediction is requested.
* Symptom text is cleaned via :func:`~app.ai.utils.text_cleaner.symptoms_to_string`
  — the **same** function used during training.  This guarantees zero
  training-serving skew.
* All exceptions surface as :exc:`ValueError` (bad input) or
  :exc:`RuntimeError` (artefact / model failure).  The route layer catches
  these and converts them to the appropriate HTTP status codes.

Usage as a script
-----------------
Run from the ``backend/`` directory to verify the inference engine::

    python -m app.ai.inference.predictor
"""

import importlib
import logging
import sys
from pathlib import Path
from typing import Any

try:
    import joblib  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - fallback when joblib is unavailable
    joblib = None  # type: ignore[assignment]

# Load lazily: import the module even when joblib is unavailable, and fail only
# when model artefacts are actually requested.

try:
    import numpy as _numpy  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - dependency is required at runtime
    _numpy = None  # type: ignore[assignment]

try:
    from app.ai.models.prediction_result import PredictionResult
except ImportError:
    from dataclasses import dataclass, field

    @dataclass
    class PredictionResult:
        disease: str
        confidence: float
        top_predictions: list[dict[str, Any]] = field(default_factory=list)

try:
    from app.ai.providers.gemini_prediction_provider import GeminiPredictionProvider
except (ImportError, ModuleNotFoundError):  # pragma: no cover - provider is optional at import time
    class GeminiPredictionProvider:  # type: ignore[no-redef]
        """Fallback provider used when the Gemini implementation is unavailable."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self._error = RuntimeError(
                "Gemini prediction provider is unavailable. "
                "Install the provider module or ensure the app.ai.providers package is present."
            )

        def predict(self, *args: Any, **kwargs: Any) -> Any:
            raise self._error

try:
    from app.ai.utils.text_cleaner import symptoms_to_string
except ImportError:  # pragma: no cover - fallback when the utility module is unavailable
    def symptoms_to_string(symptoms: list[str]) -> str:
        """Simple fallback symptom normaliser used when the training utility is absent."""
        if not isinstance(symptoms, list):
            raise ValueError(
                f"'symptoms' must be a list of strings, got {type(symptoms).__name__}."
            )

        cleaned: list[str] = []
        for symptom in symptoms:
            if isinstance(symptom, str):
                text = symptom.strip()
                if text:
                    cleaned.append(text.lower())

        return " ".join(cleaned)

if _numpy is not None:
    np = _numpy
else:  # pragma: no cover - defensive fallback when NumPy is unavailable
    class _MissingNumpy:
        def __getattr__(self, name: str):
            raise RuntimeError(
                "NumPy is required for model inference. Install the project dependencies."
            )

    np = _MissingNumpy()  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_THIS_DIR: Path = Path(__file__).resolve().parent
_BACKEND_DIR: Path = _THIS_DIR.parents[2]          # backend/
_MODELS_DIR: Path = _BACKEND_DIR / "app" / "ai" / "models"

_CLASSIFIER_PATH: Path = _MODELS_DIR / "disease_classifier.pkl"
_VECTORIZER_PATH: Path = _MODELS_DIR / "tfidf_vectorizer.pkl"
_ENCODER_PATH: Path = _MODELS_DIR / "label_encoder.pkl"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TOP_N: int = 3
_MIN_SYMPTOMS: int = 1

# ---------------------------------------------------------------------------
# DiseasePredictor class
# ---------------------------------------------------------------------------


class DiseasePredictor:
    """Lazy-loading inference engine for disease prediction."""

    def __init__(self) -> None:
        self._classifier: Any = None
        self._vectorizer: Any = None
        self._encoder: Any = None

        self._loaded: bool = False
        self._gemini = GeminiPredictionProvider()

        logger.debug(
            "DiseasePredictor instantiated. Artefacts will be loaded on first predict() call."
        )

    # ── Private: artefact loading ─────────────────────────────────────────────

    def _load_artefacts(self) -> None:
        artefacts: dict[str, Path] = {
            "vectorizer": _VECTORIZER_PATH,
            "encoder":    _ENCODER_PATH,
            "classifier": _CLASSIFIER_PATH,
        }
        missing: list[str] = [
            name for name, path in artefacts.items() if not path.exists()
        ]
        if missing:
            raise FileNotFoundError(
                f"Missing model artefact(s): {missing}. "
                f"Run 'python -m app.ai.training.train_model' to generate them."
            )

        logger.info("Loading model artefacts from: %s", _MODELS_DIR)

        try:
            self._vectorizer = joblib.load(_VECTORIZER_PATH)
            logger.info("Loaded vectorizer   ← %s", _VECTORIZER_PATH.name)

            self._encoder = joblib.load(_ENCODER_PATH)
            logger.info(
                "Loaded encoder      ← %s  (%d classes)",
                _ENCODER_PATH.name,
                len(self._encoder.classes_),
            )

            self._classifier = joblib.load(_CLASSIFIER_PATH)
            logger.info(
                "Loaded classifier   ← %s  (%s)",
                _CLASSIFIER_PATH.name,
                type(self._classifier).__name__,
            )

        except Exception as exc:
            raise RuntimeError(
                f"Failed to load model artefact: {exc}. "
                "The file may be corrupt or incompatible with the installed "
                "version of scikit-learn."
            ) from exc

        self._loaded = True
        logger.info("All artefacts loaded and cached. Predictor is ready.")

    # ── Private: input validation ─────────────────────────────────────────────

    def _validate_symptoms(self, symptoms: list[str]) -> None:
        if not isinstance(symptoms, list):
            raise ValueError(
                f"'symptoms' must be a list of strings, got {type(symptoms).__name__}."
            )

        if len(symptoms) == 0:
            raise ValueError(
                "At least one symptom must be provided. The symptoms list is empty."
            )

        usable: list[str] = [
            s for s in symptoms if isinstance(s, str) and s.strip()
        ]
        if not usable:
            raise ValueError(
                "No usable symptom text found after removing blank entries. "
                "Please provide at least one non-empty symptom string."
            )

        if len(usable) < _MIN_SYMPTOMS:
            raise ValueError(
                f"At least {_MIN_SYMPTOMS} symptom(s) required, "
                f"but only {len(usable)} usable symptom(s) were found."
            )

    # ── Public: predict ───────────────────────────────────────────────────────

    def predict(self, symptoms: list[str]) -> PredictionResult:
        # Step 1: Lazy-load artefacts
        if not self._loaded:
            self._load_artefacts()

        # Step 2: Validate input
        self._validate_symptoms(symptoms)

        # Gemini Attempt with Fallback
        try:
            print("===== TRYING GEMINI =====")
            result = self._gemini.predict(symptoms)
            print("===== GEMINI SUCCESS =====")
            return result
        except Exception as exc:
            logger.warning(
                "Gemini provider failed: %s. Falling back to local Scikit-Learn model.",
                exc,
            )

        # Step 3: Clean and vectorise symptoms (LOCAL FALLBACK)
        symptom_document: str = symptoms_to_string(symptoms)

        if not symptom_document:
            raise ValueError(
                "All symptom strings were empty after text normalisation. "
                "Please provide meaningful symptom descriptions."
            )

        logger.debug("Cleaned symptom document: %r", symptom_document)

        X_input = self._vectorizer.transform([symptom_document])

        # Step 4: Predict class probabilities
        proba: np.ndarray = self._classifier.predict_proba(X_input)[0]

        if proba.ndim != 1 or len(proba) != len(self._encoder.classes_):
            raise RuntimeError(
                f"Unexpected predict_proba output shape: {proba.shape}. "
                f"Expected ({len(self._encoder.classes_)},)."
            )

        # Step 5: Extract top-N predictions
        top_indices: np.ndarray = np.argsort(proba)[-_TOP_N:][::-1]

        top_predictions: list[dict[str, Any]] = [
            {
                "disease": self._encoder.classes_[idx],
                "confidence": round(float(proba[idx]) * 100, 2),
            }
            for idx in top_indices
        ]

        # Step 6: Assemble and return result
        top_disease: str = top_predictions[0]["disease"]
        top_confidence: float = top_predictions[0]["confidence"]

        logger.info(
            "Local Model Prediction complete — top: '%s' (%.2f %%)",
            top_disease,
            top_confidence,
        )

        return PredictionResult(
            disease=top_disease,
            confidence=top_confidence,
            top_predictions=top_predictions,
        )

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def n_classes(self) -> int:
        if not self._loaded:
            return 0
        return len(self._encoder.classes_)


# Module-level singleton
disease_predictor: DiseasePredictor = DiseasePredictor()


# ---------------------------------------------------------------------------
# Script entry point — manual verification
# ---------------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    logger.info("═" * 56)
    logger.info("MediSys AI — Inference Engine Smoke Test")
    logger.info("═" * 56)

    predictor = DiseasePredictor()

    test_cases: list[list[str]] = [
        ["fever", "cough", "sore throat", "runny nose", "sneezing"],
        ["chest pain", "shortness of breath", "sweating", "nausea", "left arm pain"],
        ["excessive thirst", "frequent urination", "blurred vision", "fatigue"],
        ["persistent cough", "night sweats", "weight loss", "fever", "blood in sputum"],
    ]

    sep: str = "─" * 56
    all_passed = True

    for symptoms in test_cases:
        logger.info(sep)
        logger.info("Input symptoms : %s", symptoms)

        try:
            result = predictor.predict(symptoms)

            logger.info(
                "Top prediction : %s (%.2f %%)",
                result.disease,
                result.confidence,
            )

            logger.info("Top-%d :", _TOP_N)
            for rank, pred in enumerate(result.top_predictions, start=1):
                logger.info(
                    "  %d. %-40s %.2f %%",
                    rank,
                    pred["disease"],
                    pred["confidence"],
                )

        except Exception as exc:
            logger.error("Prediction failed: %s", exc)
            all_passed = False

    logger.info(sep)
    logger.info("Smoke test completed.")
    logger.info("Disease classes available: %d", predictor.n_classes)
    logger.info("Status: %s", "PASSED" if all_passed else "FAILED")
    logger.info("═" * 56)


if __name__ == "__main__":
    main()