"""dashboard.py
===============
Pydantic v2 response models for the MediSys Dashboard Analytics API.

All models are read-only response schemas — they are never used as
request bodies.  They follow the same style as the existing patient and
diagnosis response models.
"""

from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# GET /summary
# ---------------------------------------------------------------------------

class DashboardSummary(BaseModel):
    """High-level system-wide statistics for the dashboard home card."""

    total_patients: int = Field(
        ...,
        ge=0,
        description="Total number of patient records in the database.",
    )
    total_diagnoses: int = Field(
        ...,
        ge=0,
        description="Total number of diagnosis records in the database.",
    )
    total_report_analyses: int = Field(
        ...,
        ge=0,
        description=(
            "Total number of medical report analyses performed. "
            "Returns 0 when report analyses are not yet persisted to the database."
        ),
    )
    high_risk_patients: int = Field(
        ...,
        ge=0,
        description=(
            "Number of patients with at least one diagnosis whose confidence score "
            "exceeds the high-risk threshold (≥ 0.80)."
        ),
    )
    average_prediction_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=(
            "Mean confidence score across all AI-reviewed diagnoses, "
            "expressed as a probability (0.0–1.0). "
            "Null when no AI predictions exist yet."
        ),
    )
    pending_diagnoses: int = Field(
        ...,
        ge=0,
        description="Number of diagnosis records with status 'pending'.",
    )
    ai_reviewed_diagnoses: int = Field(
        ...,
        ge=0,
        description="Number of diagnosis records with status 'ai_reviewed'.",
    )
    doctor_reviewed_diagnoses: int = Field(
        ...,
        ge=0,
        description="Number of diagnosis records with status 'doctor_reviewed'.",
    )


# ---------------------------------------------------------------------------
# GET /disease-distribution
# ---------------------------------------------------------------------------

class DiseaseCount(BaseModel):
    """A single disease label and its prediction count."""

    disease: str = Field(..., description="Predicted disease name.")
    count: int = Field(..., ge=0, description="Number of diagnoses with this prediction.")


class DiseaseDistribution(BaseModel):
    """Disease prediction distribution across all AI-reviewed diagnoses."""

    total: int = Field(
        ...,
        ge=0,
        description="Total number of diagnoses included in this distribution.",
    )
    distribution: list[DiseaseCount] = Field(
        ...,
        description=(
            "List of disease name → count pairs, sorted by count descending. "
            "Only diagnoses with a non-null predicted_disease are included."
        ),
    )


# ---------------------------------------------------------------------------
# GET /monthly-analytics
# ---------------------------------------------------------------------------

class MonthlyDataPoint(BaseModel):
    """Counts for a single calendar month."""

    year: int = Field(..., description="Calendar year (e.g. 2026).")
    month: int = Field(..., ge=1, le=12, description="Calendar month (1–12).")
    month_label: str = Field(
        ...,
        description="Human-readable label (e.g. 'Jul 2026') for chart axes.",
    )
    new_patients: int = Field(..., ge=0)
    new_diagnoses: int = Field(..., ge=0)
    report_analyses: int = Field(
        ...,
        ge=0,
        description="Always 0 until report analyses are persisted to the database.",
    )


class MonthlyAnalytics(BaseModel):
    """Monthly trend data for patients, diagnoses, and report analyses."""

    months_returned: int = Field(
        ...,
        ge=0,
        description="Number of calendar months included in the response.",
    )
    data: list[MonthlyDataPoint] = Field(
        ...,
        description="Monthly data points ordered from oldest to newest.",
    )


# ---------------------------------------------------------------------------
# GET /model-performance
# ---------------------------------------------------------------------------

class ModelMetric(BaseModel):
    """Performance metrics for a single trained ML model."""

    model: str = Field(
        ...,
        description="Human-readable name of the trained model.",
    )

    accuracy: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Accuracy on the held-out test split.",
    )

    precision: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Weighted-average precision.",
    )

    recall: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Weighted-average recall.",
    )

    f1_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Weighted-average F1 score.",
    )


class ModelPerformance(BaseModel):
    """Performance comparison of all trained ML models."""

    best_model: str = Field(
        ...,
        description="Model with the highest accuracy.",
    )

    disease_classes: int = Field(
        ...,
        ge=0,
        description="Number of unique disease classes.",
    )

    total_samples: int = Field(
        ...,
        ge=0,
        description="Total dataset samples used during training.",
    )

    training_samples: int = Field(
        ...,
        ge=0,
        description="Number of training samples.",
    )

    testing_samples: int = Field(
        ...,
        ge=0,
        description="Number of testing samples.",
    )

    results: list[ModelMetric] = Field(
        default_factory=list,
        description="Performance metrics for all trained models.",
    )

    metrics_available: bool = Field(
        ...,
        description="Whether saved training metrics are available.",
    )

    metrics_note: Optional[str] = Field(
        default=None,
        description="Explanation when metrics are unavailable.",
    )