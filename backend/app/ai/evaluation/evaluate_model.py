"""evaluate_model.py
====================
Offline evaluation script for the MediSys disease-prediction model.

Loads the three trained artefacts from ``app/ai/models/``, reconstructs the
identical held-out test split that ``train_model.py`` produced, and reports
a full suite of classification metrics without re-fitting any object or
writing any file to disk.

The test split is reproduced by passing the **same** ``test_size``,
``random_state``, and ``stratify`` arguments to :func:`train_test_split` that
were used during training, so the evaluation is always performed on exactly
the rows the model has never seen.

Usage::

    python -m app.ai.evaluation.evaluate_model
"""

import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from app.ai.training.preprocessing import prepare_training_data

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# Anchored relative to this file so the script works regardless of the
# working directory from which it is invoked.
_THIS_DIR: Path = Path(__file__).resolve().parent
_BACKEND_DIR: Path = _THIS_DIR.parents[2]          # backend/
_MODELS_DIR: Path = _BACKEND_DIR / "app" / "ai" / "models"

REPORTS_DIR: Path = _BACKEND_DIR / "app" / "ai" / "evaluation" / "reports"

# Artefact paths — must match the filenames written by train_model.py.
_CLASSIFIER_PATH: Path = _MODELS_DIR / "disease_classifier.pkl"
_VECTORIZER_PATH: Path = _MODELS_DIR / "tfidf_vectorizer.pkl"
_ENCODER_PATH: Path = _MODELS_DIR / "label_encoder.pkl"

# ---------------------------------------------------------------------------
# Split constants — must be byte-for-byte identical to train_model.py values.
# ---------------------------------------------------------------------------

_TEST_SIZE: float = 0.2
_RANDOM_STATE: int = 42

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class EvaluationResult:
    """Container for every metric produced by :func:`evaluate`.

    Args:
        accuracy: Fraction of test samples classified correctly (0.0–1.0).
        precision: Weighted-average precision across all disease classes.
        recall: Weighted-average recall across all disease classes.
        f1: Weighted-average F1-score across all disease classes.
        classification_report_str: Full per-class sklearn classification report.
        n_test: Number of test samples evaluated.
        n_classes: Total number of disease classes in the encoder.
        class_names: Alphabetically sorted list of disease class name strings.
    """

    accuracy: float
    precision: float
    recall: float
    f1: float
    classification_report_str: str
    n_test: int
    n_classes: int
    class_names: list[str]


# ---------------------------------------------------------------------------
# Helper: load_models
# ---------------------------------------------------------------------------


def load_models() -> Tuple[object, object, LabelEncoder]:
    """Load all three trained artefacts from ``app/ai/models/``.

    The artefacts are loaded in dependency order: vectoriser first (needed
    to transform features), then encoder (needed to decode predictions), then
    classifier (needs transformed features to predict).

    Returns:
        A three-tuple ``(classifier, vectorizer, encoder)``:

        - **classifier**: The fitted scikit-learn classifier loaded from
          ``disease_classifier.pkl``.
        - **vectorizer**: The fitted ``TfidfVectorizer`` loaded from
          ``tfidf_vectorizer.pkl``.
        - **encoder**: The fitted ``LabelEncoder`` loaded from
          ``label_encoder.pkl``.

    Raises:
        FileNotFoundError: If any of the three ``.pkl`` files is missing.
        Exception: If ``joblib.load`` fails to deserialise an artefact
            (e.g. version mismatch or corrupt file).
    """
    artefacts = {
        "vectorizer": _VECTORIZER_PATH,
        "encoder":    _ENCODER_PATH,
        "classifier": _CLASSIFIER_PATH,
    }

    # Verify all files exist before attempting to load any of them, so the
    # error message names every missing file in a single pass.
    missing = [name for name, path in artefacts.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing artefact(s): {missing}. "
            f"Run 'python -m app.ai.training.train_model' first."
        )

    logger.info("Loading artefacts from: %s", _MODELS_DIR)

    try:
        vectorizer = joblib.load(_VECTORIZER_PATH)
        logger.info("Loaded vectorizer  ← %s", _VECTORIZER_PATH.name)

        encoder: LabelEncoder = joblib.load(_ENCODER_PATH)
        logger.info("Loaded encoder     ← %s", _ENCODER_PATH.name)

        classifier = joblib.load(_CLASSIFIER_PATH)
        logger.info(
            "Loaded classifier  ← %s  (%s)",
            _CLASSIFIER_PATH.name,
            type(classifier).__name__,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Failed to deserialise artefact: {exc}. "
            "The file may be corrupt or incompatible with the current "
            "scikit-learn version."
        ) from exc

    return classifier, vectorizer, encoder


# ---------------------------------------------------------------------------
# Helper: load_dataset
# ---------------------------------------------------------------------------


def load_dataset() -> Tuple[pd.Series, pd.Series]:
    """Load and preprocess the dataset, then return ``(X, y)`` Series.

    Delegates entirely to :func:`~app.ai.training.preprocessing.prepare_training_data`
    so that the exact same cleaning logic and column validation applied at
    training time is reused here.  No independent CSV reading or text cleaning
    is performed in this function.

    Returns:
        A two-tuple ``(X, y)``:

        - **X** ``pd.Series[str]``: Cleaned, space-separated symptom strings.
        - **y** ``pd.Series[str]``: Corresponding disease label strings.

    Raises:
        FileNotFoundError: Propagated if the dataset CSV does not exist.
        ValueError: Propagated if required columns are absent from the CSV.
    """
    logger.info("Loading and preprocessing dataset via preprocessing pipeline …")
    X, y = prepare_training_data()
    logger.info("Dataset loaded: %d samples, %d unique classes.", len(X), y.nunique())
    return X, y


# ---------------------------------------------------------------------------
# Helper: evaluate
# ---------------------------------------------------------------------------


def evaluate(
    classifier: object,
    vectorizer: object,
    encoder: LabelEncoder,
    X: pd.Series,
    y: pd.Series,
) -> EvaluationResult:
    """Reconstruct the held-out test split and compute all evaluation metrics.

    The split is reproduced with the same ``test_size``, ``random_state``, and
    ``stratify`` values used in ``train_model.py``.  The saved TF-IDF
    vectorizer is used to **transform** (not fit) the test features so that
    the vocabulary and IDF weights are identical to those seen at training time.

    Args:
        classifier: Fitted scikit-learn classifier loaded from disk.
        vectorizer: Fitted ``TfidfVectorizer`` loaded from disk.
        encoder: Fitted ``LabelEncoder`` loaded from disk.
        X: Full cleaned symptom Series (training + test combined).
        y: Full disease label Series (training + test combined).

    Returns:
        :class:`EvaluationResult` containing accuracy, weighted precision,
        recall, F1, the full classification report string, and summary counts.

    Raises:
        ValueError: If ``X`` and ``y`` have different lengths.
    """
    if len(X) != len(y):
        raise ValueError(
            f"Feature and label Series must have equal length "
            f"(got {len(X)} and {len(y)})."
        )

    n_classes: int = len(encoder.classes_)
    logger.info(
        "Reproducing train/test split: test_size=%.0f%%, random_state=%d, stratified.",
        _TEST_SIZE * 100,
        _RANDOM_STATE,
    )

    # ── Step 1: Encode labels ─────────────────────────────────────────────────
    # Re-use the saved encoder so integer indices are identical to training.
    y_encoded: np.ndarray = encoder.transform(y)

    # ── Step 2: Reproduce identical split ─────────────────────────────────────
    # stratify=y_encoded mirrors the stratification used in train_model.py,
    # guaranteeing that X_test here contains exactly the same rows as X_test
    # during training.
    _, X_test, _, y_test = train_test_split(
        X,
        y_encoded,
        test_size=_TEST_SIZE,
        random_state=_RANDOM_STATE,
        stratify=y_encoded,
    )
    n_test: int = len(X_test)
    logger.info("Test split: %d samples.", n_test)

    # ── Step 3: Vectorise test features ───────────────────────────────────────
    # transform() only — the saved vectorizer's vocabulary and IDF weights
    # must not be altered.  fit_transform() here would constitute data leakage
    # and would produce different feature indices.
    logger.info("Transforming test features with saved TF-IDF vectorizer …")
    X_test_tfidf = vectorizer.transform(X_test)

    # ── Step 4: Predict ───────────────────────────────────────────────────────
    logger.info("Running predictions on test split …")
    y_pred: np.ndarray = classifier.predict(X_test_tfidf)

    # ── Step 5: Compute metrics ───────────────────────────────────────────────
    # All multi-class metrics use weighted averaging so that per-class scores
    # are weighted by the true number of instances in each class.
    logger.info("Computing evaluation metrics …")

    accuracy: float  = accuracy_score(y_test, y_pred)
    precision: float = precision_score(
        y_test, y_pred, average="weighted", zero_division=0
    )
    recall: float    = recall_score(
        y_test, y_pred, average="weighted", zero_division=0
    )
    f1: float        = f1_score(
        y_test, y_pred, average="weighted", zero_division=0
    )

    # Full per-class report — target_names maps integer indices back to
    # human-readable disease names via the saved encoder.
    report_str: str = classification_report(
        y_test,
        y_pred,
        target_names=encoder.classes_,
        zero_division=0,
        digits=4,
    )

    logger.info(
        "Metrics — Accuracy: %.4f | Precision: %.4f | Recall: %.4f | F1: %.4f",
        accuracy,
        precision,
        recall,
        f1,
    )

    return EvaluationResult(
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1=f1,
        classification_report_str=report_str,
        n_test=n_test,
        n_classes=n_classes,
        class_names=list(encoder.classes_),
    )


# ---------------------------------------------------------------------------
# Console report
# ---------------------------------------------------------------------------


def _log_report(result: EvaluationResult) -> None:
    """Emit the full evaluation report via the logger at INFO level.

    Args:
        result: The :class:`EvaluationResult` produced by :func:`evaluate`.
    """
    sep: str = "─" * 52

    logger.info(sep)
    logger.info("MediSys AI — Evaluation Report")
    logger.info(sep)
    logger.info("Test samples     : %d", result.n_test)
    logger.info("Disease classes  : %d", result.n_classes)
    logger.info(sep)
    logger.info("Accuracy         : %.4f  (%.2f %%)", result.accuracy,  result.accuracy  * 100)
    logger.info("Precision (wtd)  : %.4f  (%.2f %%)", result.precision, result.precision * 100)
    logger.info("Recall    (wtd)  : %.4f  (%.2f %%)", result.recall,    result.recall    * 100)
    logger.info("F1-score  (wtd)  : %.4f  (%.2f %%)", result.f1,        result.f1        * 100)
    logger.info(sep)
    logger.info("Per-class Classification Report:\n\n%s", result.classification_report_str)

def save_report(result: EvaluationResult) -> None:
    """Save evaluation report to a text file."""

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_path = REPORTS_DIR / f"evaluation_{timestamp}.txt"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("MediSys AI - Evaluation Report\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"Test Samples      : {result.n_test}\n")
        f.write(f"Disease Classes   : {result.n_classes}\n\n")

        f.write(f"Accuracy          : {result.accuracy:.4f}\n")
        f.write(f"Precision         : {result.precision:.4f}\n")
        f.write(f"Recall            : {result.recall:.4f}\n")
        f.write(f"F1 Score          : {result.f1:.4f}\n\n")

        f.write("=" * 60 + "\n")
        f.write("Classification Report\n")
        f.write("=" * 60 + "\n\n")

        f.write(result.classification_report_str)

    logger.info("Evaluation report saved → %s", report_path)

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Orchestrate the full evaluation pipeline.

    Steps:
        1. Configure logging.
        2. Load artefacts via :func:`load_models`.
        3. Load dataset via :func:`load_dataset`.
        4. Evaluate via :func:`evaluate`.
        5. Emit the full report via :func:`_log_report`.

    Exits with code 1 on any handled error so CI pipelines can detect
    evaluation failures from the process exit code.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    logger.info("═" * 52)
    logger.info("MediSys AI — Evaluation pipeline starting …")
    logger.info("═" * 52)

    try:
        # Load trained artefacts from disk.
        classifier, vectorizer, encoder = load_models()

        # Load and preprocess the dataset using the shared pipeline.
        X, y = load_dataset()

        # Reproduce the identical test split and compute all metrics.
        result = evaluate(classifier, vectorizer, encoder, X, y)

        # Emit the full report.
        _log_report(result)
        save_report(result)

    except FileNotFoundError as exc:
        logger.error("File not found: %s", exc)
        sys.exit(1)
    except RuntimeError as exc:
        logger.error("Artefact loading error: %s", exc)
        sys.exit(1)
    except ValueError as exc:
        logger.error("Dataset error: %s", exc)
        sys.exit(1)
    except Exception as exc:
        logger.exception("Unexpected error during evaluation: %s", exc)
        sys.exit(1)

    logger.info("Evaluation pipeline completed successfully.")


# ---------------------------------------------------------------------------
# Script entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()