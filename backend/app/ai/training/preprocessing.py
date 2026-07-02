"""
preprocessing.py
================
Data loading and preprocessing pipeline for the MediSys disease-prediction model.

This module is the **sole** consumer of ``disease_dataset.csv`` and the
**sole** producer of cleaned training data.  It is imported by
``train_model.py`` and can also be run directly as a script for quick
validation of the dataset.

Design contract
---------------
* All symptom text is cleaned via :func:`~app.ai.utils.text_cleaner.symptoms_to_string`
  — the **same** function used by ``predictor.py`` at inference time.
  This guarantees zero skew between training and serving.
* No ML objects (vectorizer, classifier, encoder) are created here.
  This file is pure data preparation.
* Callers receive either a cleaned :class:`pandas.DataFrame` or a pair of
  ``(X, y)`` Series, depending on their needs.

Usage as a script
-----------------
Run from the ``backend/`` directory to validate the dataset and preview
the cleaned output::

    python -m app.ai.training.preprocessing
"""

import logging
from pathlib import Path
from typing import Tuple

import pandas as pd

from app.ai.utils.text_cleaner import symptoms_to_string

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# Anchor all paths relative to this file so the module works regardless of
# the current working directory when it is imported or run as a script.
_THIS_DIR: Path = Path(__file__).resolve().parent
_BACKEND_DIR: Path = _THIS_DIR.parents[2]          # backend/
_DATA_DIR: Path = _BACKEND_DIR / "app" / "ai" / "data"
DATASET_PATH: Path = _DATA_DIR / "clean_dataset.csv"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# The two columns that must be present in the CSV.  Any other columns are
# silently ignored so the module stays forward-compatible if new columns are
# added to the dataset in future.
REQUIRED_COLUMNS: Tuple[str, ...] = ("symptoms", "disease")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _validate_columns(df: pd.DataFrame) -> None:
    """Raise :exc:`ValueError` if any required column is absent.

    Parameters
    ----------
    df:
        DataFrame loaded from the CSV before any processing has been applied.

    Raises
    ------
    ValueError
        With the names of every missing column so the caller can fix the CSV
        in one pass rather than discovering missing columns one at a time.
    """
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"Dataset is missing required column(s): {missing}. "
            f"Found columns: {list(df.columns)}"
        )


def _clean_symptom_row(raw_symptom_string: str) -> str:
    """Clean a single row's symptom string using the shared text-cleaner.

    The CSV stores symptoms as a space-separated string
    (e.g. ``"fever cough sore throat"``).  This function:

    1. Splits the string into individual tokens.
    2. Passes the token list through :func:`~app.ai.utils.text_cleaner.symptoms_to_string`,
       which applies :func:`~app.ai.utils.text_cleaner.clean_text` to each
       token, deduplicates, and rejoins.

    Using ``symptoms_to_string`` here — rather than a simple
    ``str.lower().strip()`` — is the critical guarantee that training-time
    and inference-time preprocessing are byte-for-byte identical.

    Parameters
    ----------
    raw_symptom_string:
        A single cell from the ``symptoms`` column.

    Returns
    -------
    str
        Cleaned, space-separated symptom string ready for TF-IDF.
    """
    # Split the raw string into tokens and pass them through the shared cleaner.
    tokens = str(raw_symptom_string).split()
    return symptoms_to_string(tokens)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_and_preprocess_data() -> pd.DataFrame:
    """Load the disease dataset CSV and return a fully cleaned DataFrame.

    Pipeline steps
    --------------
    1. **Load** — read ``disease_dataset.csv`` with UTF-8 encoding.
    2. **Validate** — assert that ``symptoms`` and ``disease`` columns exist.
    3. **Select** — keep only the two required columns; discard any extras.
    4. **Drop nulls** — remove rows where either column is missing or NaN.
    5. **Drop duplicates** — remove exact duplicate ``(symptoms, disease)`` pairs.
    6. **Clean symptoms** — apply the shared text-cleaner to every symptom string.
    7. **Drop empty symptoms** — remove any rows whose symptom string became
       empty after cleaning (e.g. a row that contained only punctuation).
    8. **Reset index** — return a contiguous 0-based index.

    Logging
    -------
    Emits ``INFO``-level log lines reporting:

    * Path of the loaded file.
    * Original row count.
    * Rows removed due to null values.
    * Rows removed as duplicates.
    * Rows removed because symptom string was empty after cleaning.
    * Final row count.
    * Number of unique disease classes.

    Parameters
    ----------
    None

    Returns
    -------
    pandas.DataFrame
        Cleaned DataFrame with exactly two columns:

        ``symptoms`` : str
            Cleaned, space-separated symptom string (TF-IDF ready).
        ``disease`` : str
            Disease label, stripped of leading/trailing whitespace.

    Raises
    ------
    FileNotFoundError
        If ``disease_dataset.csv`` does not exist at the expected path.
    ValueError
        If the CSV is missing required columns.
    """
    # ── Step 1: Load ─────────────────────────────────────────────────────────
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at: {DATASET_PATH}\n"
            "Place 'disease_dataset.csv' in app/ai/data/ before training."
        )

    logger.info("Loading dataset from: %s", DATASET_PATH)
    df = pd.read_csv(DATASET_PATH, encoding="utf-8")
    original_count: int = len(df)
    logger.info("Loaded %d rows, %d columns.", original_count, len(df.columns))

    # ── Step 2: Validate columns ──────────────────────────────────────────────
    _validate_columns(df)

    # ── Step 3: Select required columns only ──────────────────────────────────
    df = df[list(REQUIRED_COLUMNS)].copy()

    # ── Step 4: Drop rows with null / NaN values ──────────────────────────────
    count_before_null_drop: int = len(df)
    df.dropna(subset=list(REQUIRED_COLUMNS), inplace=True)
    null_rows_removed: int = count_before_null_drop - len(df)

    if null_rows_removed:
        logger.info(
            "Removed %d row(s) containing null values.", null_rows_removed
        )
    else:
        logger.info("No null values found.")

    # ── Step 5: Drop duplicate rows ───────────────────────────────────────────
    count_before_dedup: int = len(df)
    df.drop_duplicates(inplace=True)
    duplicate_rows_removed: int = count_before_dedup - len(df)

    if duplicate_rows_removed:
        logger.info(
            "Removed %d duplicate row(s).", duplicate_rows_removed
        )
    else:
        logger.info("No duplicate rows found.")

    # ── Step 6: Clean symptom text ────────────────────────────────────────────
    # Apply the shared cleaner to every cell in the symptoms column.
    # Using .apply() keeps this readable and pandas-idiomatic.
    df["symptoms"] = df["symptoms"].apply(_clean_symptom_row)

    # Also strip whitespace from disease labels for consistency.
    df["disease"] = df["disease"].str.strip()

    # ── Step 7: Drop rows where cleaned symptom is empty ─────────────────────
    count_before_empty_drop: int = len(df)
    df = df[df["symptoms"].str.len() > 0]
    empty_rows_removed: int = count_before_empty_drop - len(df)

    if empty_rows_removed:
        logger.warning(
            "Removed %d row(s) whose symptom string was empty after cleaning.",
            empty_rows_removed,
        )

    # ── Step 8: Reset index ───────────────────────────────────────────────────
    df.reset_index(drop=True, inplace=True)

    # ── Summary log ───────────────────────────────────────────────────────────
    final_count: int = len(df)
    total_removed: int = original_count - final_count
    unique_diseases: int = df["disease"].nunique()

    logger.info(
        "Preprocessing complete. "
        "Original: %d rows | Removed: %d rows (nulls=%d, duplicates=%d, empty=%d) "
        "| Final: %d rows | Disease classes: %d",
        original_count,
        total_removed,
        null_rows_removed,
        duplicate_rows_removed,
        empty_rows_removed,
        final_count,
        unique_diseases,
    )

    return df


def prepare_training_data(
    df: pd.DataFrame | None = None,
) -> Tuple[pd.Series, pd.Series]:
    """Return ``(X, y)`` Series ready for TF-IDF vectorisation and model training.

    This is a thin convenience wrapper around :func:`load_and_preprocess_data`
    that splits the cleaned DataFrame into its feature and label components.

    Parameters
    ----------
    df:
        Optional pre-loaded, pre-cleaned DataFrame.  When supplied, this
        function skips the load-and-preprocess step and uses *df* directly.
        Callers that have already called :func:`load_and_preprocess_data`
        should pass the result here to avoid re-reading the CSV.
        When ``None`` (the default), :func:`load_and_preprocess_data` is
        called internally.

    Returns
    -------
    X : pandas.Series of str
        Cleaned symptom strings — one document per row.
        Suitable for ``TfidfVectorizer.fit_transform(X)``.

    y : pandas.Series of str
        Disease label for each row.
        Suitable for ``LabelEncoder.fit_transform(y)``.

    Raises
    ------
    FileNotFoundError
        Propagated from :func:`load_and_preprocess_data` if the CSV is absent.
    ValueError
        Propagated from :func:`load_and_preprocess_data` if columns are missing.

    Examples
    --------
    >>> X, y = prepare_training_data()
    >>> print(X.iloc[0])
    'fever cough sore throat runny nose sneezing'
    >>> print(y.iloc[0])
    'Common Cold'
    >>> print(f"{len(X)} samples, {y.nunique()} classes")
    '274 samples, 45 classes'
    """
    if df is None:
        df = load_and_preprocess_data()

    X: pd.Series = df["symptoms"]
    y: pd.Series = df["disease"]

    logger.info(
        "Training data prepared: %d samples, %d unique classes.",
        len(X),
        y.nunique(),
    )

    return X, y


# ---------------------------------------------------------------------------
# Script entry point — for manual validation
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    df = load_and_preprocess_data()
    X, y = prepare_training_data(df)

    print("\n── Dataset preview (first 5 rows) ──────────────────────────────")
    print(df.head().to_string(index=True))

    print("\n── Disease class distribution ───────────────────────────────────")
    print(y.value_counts().to_string())

    print(f"\n── Summary ──────────────────────────────────────────────────────")
    print(f"  Total samples   : {len(X)}")
    print(f"  Unique diseases : {y.nunique()}")
    print(f"  Dataset path    : {DATASET_PATH}")