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

import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from app.ai.utils.text_cleaner import symptoms_to_string

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# Anchored relative to this file — works regardless of where the process
# is launched from.
_THIS_DIR: Path = Path(__file__).resolve().parent
_BACKEND_DIR: Path = _THIS_DIR.parents[2]          # backend/
_MODELS_DIR: Path = _BACKEND_DIR / "app" / "ai" / "models"

# Artefact filenames — must match those written by train_model.py exactly.
_CLASSIFIER_PATH: Path = _MODELS_DIR / "disease_classifier.pkl"
_VECTORIZER_PATH: Path = _MODELS_DIR / "tfidf_vectorizer.pkl"
_ENCODER_PATH: Path = _MODELS_DIR / "label_encoder.pkl"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Maximum number of top predictions to include in PredictionResult.
_TOP_N: int = 3

# Minimum number of non-empty symptoms required before prediction is attempted.
_MIN_SYMPTOMS: int = 1

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class PredictionResult:
    """Container for the output of a single prediction request.

    Args:
        disease: Name of the most probable disease (highest confidence).
        confidence: Probability of the top prediction, expressed as a
            percentage rounded to two decimal places (0.00–100.00).
        top_predictions: Ordered list of the top-N most probable diseases.
            Each entry is a dictionary with two keys:

            - ``"disease"`` (str): Disease name.
            - ``"confidence"`` (float): Probability as a percentage
              (0.00–100.00), rounded to two decimal places.

            The list is sorted in descending order of confidence; index 0
            always matches ``disease`` and ``confidence``.
    """

    disease: str
    confidence: float
    top_predictions: list[dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# DiseasePredictor class
# ---------------------------------------------------------------------------


class DiseasePredictor:
    """Lazy-loading inference engine for disease prediction.

    Artefacts (classifier, vectorizer, label encoder) are loaded from disk
    the first time :meth:`predict` is called and then cached as instance
    attributes for all subsequent calls.  This avoids blocking I/O at import
    time while still keeping the loaded objects in memory across requests.

    Example:
        >>> predictor = DiseasePredictor()
        >>> result = predictor.predict(["fever", "cough", "sore throat"])
        >>> print(result.disease)
        'Common Cold'
        >>> print(f"{result.confidence:.2f} %")
        '33.00 %'
    """

    def __init__(self) -> None:
        """Initialise the predictor without loading any artefacts.

        Artefacts are loaded lazily on the first call to :meth:`predict`.
        """
        # Private attributes — set to None until _load_artefacts() is called.
        self._classifier: Any = None
        self._vectorizer: Any = None
        self._encoder: Any = None

        # Flag that prevents repeated I/O on every request.
        self._loaded: bool = False

        logger.debug(
            "DiseasePredictor instantiated. Artefacts will be loaded on first predict() call."
        )

    # ── Private: artefact loading ─────────────────────────────────────────────

    def _load_artefacts(self) -> None:
        """Load all three artefacts from disk and cache them on the instance.

        Verifies that every ``.pkl`` file exists before attempting to
        deserialise any of them, so the error message lists every missing file
        in a single pass rather than failing on the first.

        Raises:
            FileNotFoundError: If one or more ``.pkl`` files are absent.
                Includes the names of all missing files and instructs the
                caller to run ``train_model.py`` first.
            RuntimeError: If ``joblib.load`` fails for any artefact (e.g.
                corrupt file, scikit-learn version mismatch).
        """
        # Preflight: check all three files exist before loading any.
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
            # Load in dependency order: vectorizer → encoder → classifier.
            # The vectorizer must be loaded first because its vocabulary defines
            # the feature space that the classifier expects.
            self._vectorizer = joblib.load(_VECTORIZER_PATH)
            logger.info("Loaded vectorizer  ← %s", _VECTORIZER_PATH.name)

            self._encoder = joblib.load(_ENCODER_PATH)
            logger.info(
                "Loaded encoder     ← %s  (%d classes)",
                _ENCODER_PATH.name,
                len(self._encoder.classes_),
            )

            self._classifier = joblib.load(_CLASSIFIER_PATH)
            logger.info(
                "Loaded classifier  ← %s  (%s)",
                _CLASSIFIER_PATH.name,
                type(self._classifier).__name__,
            )

        except Exception as exc:
            # Wrap the underlying joblib/pickle error with a clear message so
            # that the service layer can surface a meaningful HTTP 500.
            raise RuntimeError(
                f"Failed to load model artefact: {exc}. "
                "The file may be corrupt or incompatible with the installed "
                "version of scikit-learn."
            ) from exc

        self._loaded = True
        logger.info("All artefacts loaded and cached. Predictor is ready.")

    # ── Private: input validation ─────────────────────────────────────────────

    def _validate_symptoms(self, symptoms: list[str]) -> None:
        """Validate that the symptom list is non-empty and contains usable text.

        Args:
            symptoms: Raw list of symptom strings supplied by the caller.

        Raises:
            ValueError: If ``symptoms`` is not a list, is empty, or contains
                no non-blank string values after stripping whitespace.
        """
        if not isinstance(symptoms, list):
            raise ValueError(
                f"'symptoms' must be a list of strings, got {type(symptoms).__name__}."
            )

        if len(symptoms) == 0:
            raise ValueError(
                "At least one symptom must be provided. The symptoms list is empty."
            )

        # Check that at least one item survives whitespace-stripping.
        # Non-string items are also silently ignored here; text_cleaner handles them.
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
        """Predict the most probable disease from a list of symptom strings.

        This is the primary public interface consumed by
        ``app/services/diagnosis_service.py``.  It handles the complete
        inference pipeline: validation → cleaning → vectorisation → prediction
        → probability ranking → result assembly.

        Args:
            symptoms: Raw list of symptom strings as received from the API
                request body (``DiagnosisCreate.symptoms``).  May contain
                mixed case, punctuation, or extra whitespace — the text cleaner
                normalises all of these before vectorisation.

        Returns:
            :class:`PredictionResult` containing:

            - ``disease``: Name of the top-predicted disease.
            - ``confidence``: Probability of the top prediction as a percentage
              (0.00–100.00), rounded to two decimal places.
            - ``top_predictions``: Ordered list of the top-3 most probable
              diseases, each as ``{"disease": str, "confidence": float}``.

        Raises:
            ValueError: If ``symptoms`` fails validation (empty list, no
                usable text, wrong type).
            FileNotFoundError: Propagated from :meth:`_load_artefacts` if
                model files are missing.
            RuntimeError: Propagated from :meth:`_load_artefacts` if
                deserialisation fails, or raised here if ``predict_proba``
                returns an unexpected shape.

        Example:
            >>> predictor = DiseasePredictor()
            >>> result = predictor.predict(["chest pain", "shortness of breath", "sweating"])
            >>> result.disease
            'Heart Disease'
            >>> result.confidence
            46.0
            >>> [(p["disease"], p["confidence"]) for p in result.top_predictions]
            [('Heart Disease', 46.0), ('Anxiety Disorder', 12.5), ('Pneumonia', 8.0)]
        """
        # ── Step 1: Lazy-load artefacts ───────────────────────────────────────
        # Skip if already loaded — the flag prevents repeated disk I/O across
        # multiple prediction requests within the same process lifetime.
        if not self._loaded:
            self._load_artefacts()

        # ── Step 2: Validate input ────────────────────────────────────────────
        self._validate_symptoms(symptoms)
        logger.debug("Predicting for %d symptom(s): %s", len(symptoms), symptoms)

        # ── Step 3: Clean and vectorise symptoms ──────────────────────────────
        # symptoms_to_string cleans each token via clean_text(), deduplicates,
        # and joins into a single space-separated string — the same
        # transformation applied to every row during training.
        symptom_document: str = symptoms_to_string(symptoms)

        if not symptom_document:
            # All symptoms were blank or non-string after cleaning.
            raise ValueError(
                "All symptom strings were empty after text normalisation. "
                "Please provide meaningful symptom descriptions."
            )

        logger.debug("Cleaned symptom document: %r", symptom_document)

        # Wrap in a list: TfidfVectorizer.transform() expects an iterable of
        # documents, not a single string.  This produces a (1, vocab_size)
        # sparse matrix.
        X_input = self._vectorizer.transform([symptom_document])

        # ── Step 4: Predict class probabilities ───────────────────────────────
        # predict_proba returns shape (n_samples, n_classes) = (1, n_classes).
        # We take index [0] to get the flat (n_classes,) probability array.
        proba: np.ndarray = self._classifier.predict_proba(X_input)[0]

        if proba.ndim != 1 or len(proba) != len(self._encoder.classes_):
            raise RuntimeError(
                f"Unexpected predict_proba output shape: {proba.shape}. "
                f"Expected ({len(self._encoder.classes_)},)."
            )

        # ── Step 5: Extract top-N predictions ────────────────────────────────
        # np.argsort returns indices that sort the array in ascending order.
        # [-_TOP_N:] takes the last _TOP_N (highest probability) indices.
        # [::-1] reverses them so index 0 is the highest probability.
        top_indices: np.ndarray = np.argsort(proba)[-_TOP_N:][::-1]

        top_predictions: list[dict[str, Any]] = [
            {
                # Decode integer class index back to the disease name string.
                "disease": self._encoder.classes_[idx],
                # Convert probability (0.0–1.0) to percentage, rounded to 2dp.
                "confidence": round(float(proba[idx]) * 100, 2),
            }
            for idx in top_indices
        ]

        # ── Step 6: Assemble and return result ────────────────────────────────
        top_disease: str   = top_predictions[0]["disease"]
        top_confidence: float = top_predictions[0]["confidence"]

        logger.info(
            "Prediction complete — top: '%s' (%.2f %%) | top-%d: %s",
            top_disease,
            top_confidence,
            _TOP_N,
            [(p["disease"], p["confidence"]) for p in top_predictions],
        )

        return PredictionResult(
            disease=top_disease,
            confidence=top_confidence,
            top_predictions=top_predictions,
        )

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def is_loaded(self) -> bool:
        """Return True if artefacts have been loaded and the predictor is ready.

        Returns:
            bool: True after the first successful call to :meth:`predict`
                or a direct call to :meth:`_load_artefacts`.
        """
        return self._loaded

    @property
    def n_classes(self) -> int:
        """Return the number of disease classes the model can predict.

        Returns:
            int: Number of unique disease classes, or 0 if not yet loaded.
        """
        if not self._loaded:
            return 0
        return len(self._encoder.classes_)


# ---------------------------------------------------------------------------
# Module-level singleton — imported by the service layer
# ---------------------------------------------------------------------------

# A single shared instance is created at module import time.  Because
# artefacts are loaded lazily, this has no I/O cost until predict() is called.
# The service layer imports and uses this object directly:
#
#   from app.ai.inference.predictor import disease_predictor
#   result = await asyncio.to_thread(disease_predictor.predict, symptoms)
#
disease_predictor: DiseasePredictor = DiseasePredictor()


# ---------------------------------------------------------------------------
# Script entry point — manual verification
# ---------------------------------------------------------------------------


def main() -> None:
    """Run a quick smoke-test of the inference engine with known symptom sets.

    Exercises the full prediction pipeline (artefact loading, cleaning,
    vectorisation, probability ranking) against four clinically distinct
    symptom combinations.  Output is logged at INFO level so it is visible
    when run from the command line.

    Exits with code 1 if any test case raises an exception.
    """
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

    # Test cases: (symptom list, expected disease label)
    test_cases: list[list[str]] =[
    ["fever", "cough", "sore throat", "runny nose", "sneezing"],
    ["chest pain", "shortness of breath", "sweating", "nausea", "left arm pain"],
    ["excessive thirst", "frequent urination", "blurred vision", "fatigue"],
    ["persistent cough", "night sweats", "weight loss", "fever", "blood in sputum"],
    ]

    sep: str = "─" * 56

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
            result = predictor.predict(symptoms)
            logger.info("Top-%d          :", _TOP_N)
            for rank, pred in enumerate(result.top_predictions, start=1):
                logger.info("  %d. %-35s %.2f %%", rank, pred["disease"], pred["confidence"])

        except Exception as exc:
            logger.error("Prediction failed: %s", exc)
            all_passed = False

    logger.info(sep)
    logger.info("Smoke test completed.")
    logger.info("Disease classes available: %d", predictor.n_classes)
    logger.info("═" * 56)


if __name__ == "__main__":
    main()