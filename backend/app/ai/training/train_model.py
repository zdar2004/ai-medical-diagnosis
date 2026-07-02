"""
train_model.py
==============
Training pipeline for the MediSys disease-prediction classifier.

This script loads cleaned training data from :mod:`preprocessing`, fits a
TF-IDF vectoriser and a ``RandomForestClassifier``, evaluates the model on
a held-out test split, and serialises all three artefacts to
``app/ai/models/`` for use by ``inference/predictor.py``.

Pipeline summary
----------------
1. Load and preprocess data via :func:`~preprocessing.prepare_training_data`.
2. Encode string labels to integers with :class:`~sklearn.preprocessing.LabelEncoder`.
3. Split into 80 % train / 20 % test (stratified, ``random_state=42``).
4. Vectorise symptom strings with :class:`~sklearn.feature_extraction.text.TfidfVectorizer`.
5. Train a :class:`~sklearn.ensemble.RandomForestClassifier`.
6. Evaluate on the test split and report accuracy.
7. Serialise vectoriser, encoder, and classifier to ``app/ai/models/``.

Artefacts written
-----------------
``app/ai/models/disease_classifier.pkl``
    Trained ``RandomForestClassifier``.
``app/ai/models/tfidf_vectorizer.pkl``
    Fitted ``TfidfVectorizer`` — **must** be used identically at inference time.
``app/ai/models/label_encoder.pkl``
    Fitted ``LabelEncoder`` — maps integer predictions back to disease names.

Usage
-----
Run from the ``backend/`` directory::

    python -m app.ai.training.train_model
"""

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.base import ClassifierMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report
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

_THIS_DIR: Path = Path(__file__).resolve().parent
_BACKEND_DIR: Path = _THIS_DIR.parents[2]          # backend/
MODELS_DIR: Path = _BACKEND_DIR / "app" / "ai" / "models"

# Artefact filenames — must match the names read by predictor.py
CLASSIFIER_PATH: Path = MODELS_DIR / "disease_classifier.pkl"
VECTORIZER_PATH: Path = MODELS_DIR / "tfidf_vectorizer.pkl"
ENCODER_PATH: Path = MODELS_DIR / "label_encoder.pkl"

# ---------------------------------------------------------------------------
# Hyperparameters
# ---------------------------------------------------------------------------

# TF-IDF settings
# ---------------
# ngram_range=(1, 2): captures both single-word ("fever") and two-word
#   ("chest pain", "shortness breath") medical phrases.
# min_df=1: include all terms — our dataset is small so no term is truly rare.
# sublinear_tf=True: apply log(1+tf) scaling to dampen the effect of very
#   frequent words (e.g. "fever" appears across many disease classes).
TFIDF_PARAMS: dict = {
    "ngram_range": (1, 2),
    "min_df": 1,
    "sublinear_tf": True,
    "strip_accents": "unicode",
    "analyzer": "word",
}

# RandomForest settings
# ---------------------
# n_estimators=200: enough trees for a stable ensemble on a small dataset
#   without excessive memory use.
# max_depth=None: allow full tree growth; the ensemble averaging prevents
#   overfitting better than depth-limiting on small data.
# min_samples_split=2: default — appropriate for 200–300 samples.
# min_samples_leaf=1: default — every leaf may hold a single sample; the
#   forest still generalises via bagging.
# class_weight="balanced": compensates for any class-frequency imbalance
#   so minority diseases are not drowned out by common ones.
# random_state=42: reproducible results across runs.
# n_jobs=-1: use all available CPU cores to speed up training.
CLASSIFIER_PARAMS = {
    "C": 4.0,
    "max_iter": 1000,
    "class_weight": "balanced",
    "random_state": 42,
    "n_jobs": -1,
}

# Train/test split settings
TEST_SIZE: float = 0.2
RANDOM_STATE: int = 42

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class TrainingResult:
    """Container for all artefacts and metrics produced by :func:`train`.

    Attributes
    ----------
    vectorizer : TfidfVectorizer
        Fitted vectoriser.  Must be used with identical settings at inference.
    encoder : LabelEncoder
        Fitted label encoder mapping class indices ↔ disease name strings.
    classifier : RandomForestClassifier
        Trained classifier.
    train_accuracy : float
        Accuracy on the training split (0.0–1.0).
    test_accuracy : float
        Accuracy on the held-out test split (0.0–1.0).
    n_samples : int
        Total number of samples used (after preprocessing).
    n_train : int
        Number of training samples.
    n_test : int
        Number of test samples.
    n_classes : int
        Number of unique disease classes.
    class_names : list[str]
        Sorted list of disease class name strings.
    """
    vectorizer: TfidfVectorizer
    encoder: LabelEncoder
    classifier: ClassifierMixin
    train_accuracy: float
    test_accuracy: float
    n_samples: int
    n_train: int
    n_test: int
    n_classes: int
    class_names: list[str]


# ---------------------------------------------------------------------------
# Core training function
# ---------------------------------------------------------------------------

def train(
    X: pd.Series | None = None,
    y: pd.Series | None = None,
) -> TrainingResult:
    """Execute the full training pipeline and return all artefacts and metrics.

    This function is intentionally free of I/O side-effects (no file writes,
    no ``print`` calls).  All serialisation and console output is handled by
    :func:`main` so that ``train`` can be called cleanly from tests or
    notebooks.

    Parameters
    ----------
    X:
        Optional pre-loaded feature Series (cleaned symptom strings).
        When ``None``, :func:`~preprocessing.prepare_training_data` is called
        to load and preprocess the dataset automatically.
    y:
        Optional pre-loaded label Series (disease name strings).
        Must be supplied together with *X* or not at all.

    Returns
    -------
    TrainingResult
        Dataclass containing the fitted artefacts and all evaluation metrics.

    Raises
    ------
    ValueError
        If exactly one of *X* / *y* is supplied (both or neither required).
    FileNotFoundError
        Propagated from :func:`~preprocessing.prepare_training_data` if the
        dataset CSV is missing.
    """
    # ── Validate arguments ────────────────────────────────────────────────────
    if (X is None) != (y is None):
        raise ValueError("Supply both X and y, or neither.")

    # ── Step 1: Load data ─────────────────────────────────────────────────────
    if X is None:
        logger.info("Loading and preprocessing dataset …")
        X, y = prepare_training_data()

    n_samples: int = len(X)
    logger.info("Dataset ready: %d samples.", n_samples)

    # ── Step 2: Encode labels ─────────────────────────────────────────────────
    # LabelEncoder converts disease name strings → integer class indices.
    # We keep the fitted encoder so predictor.py can invert the mapping.
    logger.info("Encoding disease labels …")
    encoder = LabelEncoder()
    y_encoded: np.ndarray = encoder.fit_transform(y)
    n_classes: int = len(encoder.classes_)
    logger.info("Label encoding complete: %d unique disease classes.", n_classes)

    # ── Step 3: Train / test split ────────────────────────────────────────────
    # stratify=y_encoded ensures each class is proportionally represented in
    # both splits — essential when some classes have only 6 samples.
    logger.info(
        "Splitting data: %.0f%% train / %.0f%% test (stratified, seed=%d) …",
        (1 - TEST_SIZE) * 100,
        TEST_SIZE * 100,
        RANDOM_STATE,
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y_encoded,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y_encoded,
    )
    n_train: int = len(X_train)
    n_test: int = len(X_test)
    logger.info("Split complete: %d train, %d test.", n_train, n_test)

    # ── Step 4: TF-IDF vectorisation ──────────────────────────────────────────
    # fit_transform on training data only — never fit on test data.
    logger.info("Fitting TF-IDF vectoriser on training data …")
    vectorizer = TfidfVectorizer(**TFIDF_PARAMS)
    X_train_tfidf = vectorizer.fit_transform(X_train)

    # transform (not fit_transform) on test data — simulates inference.
    X_test_tfidf = vectorizer.transform(X_test)

    vocab_size: int = len(vectorizer.vocabulary_)
    logger.info(
        "TF-IDF complete: vocabulary size = %d features.", vocab_size
    )

    # ── Step 5: Train classifier ──────────────────────────────────────────────
    logger.info(
        "Training LogisticRegression (C=%.1f)...",
        CLASSIFIER_PARAMS["C"],
    )
    classifier = LogisticRegression(**CLASSIFIER_PARAMS)
    classifier.fit(X_train_tfidf, y_train)
    logger.info("Classifier training complete.")

    # ── Step 6: Evaluate ──────────────────────────────────────────────────────
    y_test_pred: np.ndarray = classifier.predict(X_test_tfidf)
    test_accuracy: float = accuracy_score(y_test, y_test_pred)

    logger.info(
        "Evaluation — Test accuracy: %.4f",
        test_accuracy
    )

    # Detailed per-class report at DEBUG level (not shown by default)
    report = classification_report(
        y_test,
        y_test_pred,
        target_names=encoder.classes_,
        zero_division=0,
    )
    logger.debug("Per-class classification report:\n%s", report)

    return TrainingResult(
        vectorizer=vectorizer,
        encoder=encoder,
        classifier=classifier,
        train_accuracy=None,
        test_accuracy=test_accuracy,
        n_samples=n_samples,
        n_train=n_train,
        n_test=n_test,
        n_classes=n_classes,
        class_names=list(encoder.classes_),
    )


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------

def save_artefacts(result: TrainingResult) -> None:
    """Serialise all three trained artefacts to ``app/ai/models/``.

    Creates the ``models/`` directory if it does not already exist.
    Artefacts are written atomically in the order: vectoriser → encoder →
    classifier, so a partial write (e.g. due to disk-full) leaves the
    directory in a detectable incomplete state.

    Parameters
    ----------
    result:
        The :class:`TrainingResult` returned by :func:`train`.

    Raises
    ------
    OSError
        If the models directory cannot be created or any file cannot be written.
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Saving artefacts to: %s", MODELS_DIR)

    joblib.dump(result.vectorizer, VECTORIZER_PATH)
    logger.info("Saved vectoriser  → %s", VECTORIZER_PATH.name)

    joblib.dump(result.encoder, ENCODER_PATH)
    logger.info("Saved encoder     → %s", ENCODER_PATH.name)

    joblib.dump(result.classifier, CLASSIFIER_PATH)
    logger.info("Saved classifier  → %s", CLASSIFIER_PATH.name)

    logger.info("All artefacts saved successfully.")


# ---------------------------------------------------------------------------
# Console report
# ---------------------------------------------------------------------------

def _print_report(result: TrainingResult) -> None:
    """Print a formatted training summary to stdout."""
    sep = "─" * 52

    print(f"\n{sep}")
    print("  MediSys AI — Training Report")
    print(sep)
    print(f"  Total samples      : {result.n_samples}")
    print(f"  Training samples   : {result.n_train}")
    print(f"  Testing samples    : {result.n_test}")
    print(f"  Disease classes    : {result.n_classes}")
    print(sep)
    print(f"  Testing accuracy   : {result.test_accuracy * 100:.2f} %")
    print(sep)
    print("  Artefacts saved:")
    print(f"    • {VECTORIZER_PATH.name}")
    print(f"    • {ENCODER_PATH.name}")
    print(f"    • {CLASSIFIER_PATH.name}")
    print(f"  Location: {MODELS_DIR}")
    print(sep)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the full training pipeline end-to-end and save all artefacts.

    Configures logging, calls :func:`train`, serialises artefacts via
    :func:`save_artefacts`, and prints a human-readable summary.

    Exits with code 1 on any unhandled error so CI pipelines can detect
    training failures.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    logger.info("═" * 52)
    logger.info("MediSys AI — Training pipeline starting …")
    logger.info("═" * 52)

    try:
        result = train()
        save_artefacts(result)
        _print_report(result)
    except FileNotFoundError as exc:
        logger.error("Dataset file not found: %s", exc)
        sys.exit(1)
    except ValueError as exc:
        logger.error("Data error: %s", exc)
        sys.exit(1)
    except Exception as exc:
        logger.exception("Unexpected error during training: %s", exc)
        sys.exit(1)

    logger.info("Training pipeline completed successfully.")


# ---------------------------------------------------------------------------
# Script entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()