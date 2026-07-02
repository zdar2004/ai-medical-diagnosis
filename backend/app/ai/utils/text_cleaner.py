"""
text_cleaner.py
===============
Pure preprocessing functions for medical symptom text.

Used by **both** the training pipeline (preprocessing.py / train_model.py)
and the runtime inference engine (predictor.py) to guarantee that raw
symptom strings are transformed identically in both paths.  Any divergence
between training-time and inference-time text handling causes silent accuracy
degradation; keeping all logic here in one place prevents that.

All functions are stateless and side-effect-free — safe for concurrent use
inside async FastAPI request handlers.

Standard-library only: no NLTK, spaCy, or third-party NLP dependencies.
"""

import re
import string
from typing import List


# ---------------------------------------------------------------------------
# Internal constants
# ---------------------------------------------------------------------------

# Build a translation table that maps every punctuation character to a space
# EXCEPT the hyphen (-).  Hyphens are preserved at this stage so that
# multi-word medical terms written with hyphens (e.g. "shortness-of-breath",
# "rust-colored") are not collapsed into a single unrecognisable token.
# A second pass later converts remaining hyphens to spaces.
_PUNCT_EXCEPT_HYPHEN: str = string.punctuation.replace("-", "")
_PUNCT_TABLE = str.maketrans(_PUNCT_EXCEPT_HYPHEN, " " * len(_PUNCT_EXCEPT_HYPHEN))

# Regex that matches two or more consecutive whitespace characters (spaces,
# tabs, newlines).  Used to collapse runs of whitespace into a single space.
_MULTI_SPACE_RE = re.compile(r"\s{2,}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """Normalise a raw text string into a clean, model-ready form.

    Transformation steps (applied in order):

    1. **Lowercase** — unifies case so "Fever" and "fever" are the same token.
    2. **Remove punctuation** — strips characters such as ``!``, ``(``, ``.``
       that carry no semantic meaning for symptom classification.
       Hyphens are intentionally kept during this pass so that hyphenated
       medical terms survive intact.
    3. **Convert hyphens to spaces** — after punctuation removal, hyphens that
       separated words (e.g. ``"rust-colored"``) are replaced with a space so
       that each word becomes an independent TF-IDF token.
    4. **Collapse whitespace** — multiple consecutive spaces are reduced to one.
    5. **Strip** — removes any leading or trailing whitespace from the result.

    Medical terminology is preserved throughout: multi-syllable terms, numeric
    qualifiers (e.g. ``"stage 2"``), and compound descriptors
    (e.g. ``"shortness of breath"``) pass through unchanged because only
    punctuation characters are removed, not letters or digits.

    Parameters
    ----------
    text:
        Raw input string — may contain mixed case, punctuation, and
        irregular whitespace.

    Returns
    -------
    str
        Normalised string.  Returns an empty string if *text* is blank
        or contains only punctuation/whitespace.

    Examples
    --------
    >>> clean_text("  High Fever!! ")
    'high fever'
    >>> clean_text("Shortness-of-Breath")
    'shortness of breath'
    >>> clean_text("Chest pain (severe), radiating to arm.")
    'chest pain  severe  radiating to arm'
    """
    if not isinstance(text, str):
        return ""

    # Step 1: lowercase
    text = text.lower()

    # Step 2: remove punctuation except hyphens
    text = text.translate(_PUNCT_TABLE)

    # Step 3: convert hyphens to spaces
    text = text.replace("-", " ")

    # Step 4: collapse multiple whitespace characters
    text = _MULTI_SPACE_RE.sub(" ", text)

    # Step 5: strip leading/trailing whitespace
    return text.strip()


def tokenize(text: str) -> List[str]:
    """Split a cleaned text string into individual word tokens.

    Calls :func:`clean_text` on *text* first so that callers can pass raw
    input directly without a separate cleaning step.  Empty tokens that
    result from multiple adjacent separators are discarded.

    Parameters
    ----------
    text:
        Raw or pre-cleaned input string.

    Returns
    -------
    List[str]
        Ordered list of non-empty lowercase word tokens.
        Returns an empty list if *text* is blank or contains no words.

    Examples
    --------
    >>> tokenize("Fever, Cough  and Sore Throat!")
    ['fever', 'cough', 'and', 'sore', 'throat']
    >>> tokenize("   ")
    []
    """
    cleaned = clean_text(text)
    # str.split() with no argument splits on any whitespace and
    # automatically discards empty strings — no explicit filter needed.
    return cleaned.split()


def clean_symptoms(symptoms: List[str]) -> List[str]:
    """Clean a list of symptom strings and return a deduplicated, ordered list.

    Each symptom phrase is individually passed through :func:`clean_text`.
    Phrases that are empty after cleaning are silently discarded.
    Duplicates (after normalisation) are removed while the original
    encounter order of the *first* occurrence is preserved.

    This function is the canonical entry point for cleaning symptom lists
    coming from:

    * **Training data** — rows read from ``disease_dataset.csv``.
    * **API requests** — ``symptoms`` field from ``DiagnosisCreate``.

    Parameters
    ----------
    symptoms:
        Raw list of symptom strings.  Individual items may contain mixed
        case, punctuation, or extra whitespace.  Non-string items are
        ignored.

    Returns
    -------
    List[str]
        Cleaned, deduplicated list of symptom phrases in original order.
        Returns an empty list if all inputs are empty or non-string.

    Examples
    --------
    >>> clean_symptoms(["Fever", "COUGH", "fever", "  ", "Sore Throat!"])
    ['fever', 'cough', 'sore throat']
    >>> clean_symptoms([])
    []
    """
    seen: dict = {}  # dict preserves insertion order in Python 3.7+

    for symptom in symptoms:
        if not isinstance(symptom, str):
            continue
        cleaned = clean_text(symptom)
        if cleaned and cleaned not in seen:
            # Use the cleaned string as both key and value so we can
            # reconstruct the ordered list efficiently at the end.
            seen[cleaned] = None

    # dict.fromkeys / dict.keys() preserves insertion order.
    return list(seen.keys())


def symptoms_to_string(symptoms: List[str]) -> str:
    """Convert a list of symptom strings into a single, space-joined string.

    This is the primary function consumed by:

    * ``TfidfVectorizer.transform()`` at inference time inside
      ``predictor.py``.
    * ``TfidfVectorizer.fit_transform()`` at training time inside
      ``preprocessing.py``.

    Internally calls :func:`clean_symptoms` so that the output is always
    normalised and deduplicated regardless of input quality.

    Parameters
    ----------
    symptoms:
        Raw list of symptom strings from user input or training data.

    Returns
    -------
    str
        A single space-separated string of cleaned symptom tokens,
        suitable for direct use as a TF-IDF document.
        Returns an empty string if no valid symptoms are found.

    Examples
    --------
    >>> symptoms_to_string(["Fever", "Cough", "Sore Throat!"])
    'fever cough sore throat'
    >>> symptoms_to_string(["FEVER", "fever", "  "])
    'fever'
    >>> symptoms_to_string([])
    ''
    """
    cleaned = clean_symptoms(symptoms)
    return " ".join(cleaned)