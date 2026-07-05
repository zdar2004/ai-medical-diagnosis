"""routes/dashboard.py
======================
FastAPI router for the MediSys Dashboard Analytics API.

Exposes four read-only endpoints under ``/api/v1/dashboard``:

    GET /summary              — system-wide counts and averages
    GET /disease-distribution — per-disease prediction counts for charts
    GET /monthly-analytics    — monthly trend data for patients and diagnoses
    GET /model-performance    — ML model identity and evaluation metrics

All endpoints require Admin or Doctor role.  Staff is intentionally excluded
from dashboard access — this mirrors clinical practice where aggregate
statistics are consumed by clinicians and administrators, not reception staff.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import require_roles
from app.database import get_database
from app.models.dashboard import (
    DashboardSummary,
    DiseaseDistribution,
    ModelPerformance,
    MonthlyAnalytics,
)
from app.models.user import UserInDB, UserRole
from app.services.dashboard_service import DashboardService

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard Analytics"],
)

# ---------------------------------------------------------------------------
# Dependency injection
# ---------------------------------------------------------------------------


def _svc(db: AsyncIOMotorDatabase = Depends(get_database)) -> DashboardService:
    """Inject DashboardService with the live DB handle."""
    return DashboardService(db)


# ---------------------------------------------------------------------------
# GET /summary
# ---------------------------------------------------------------------------

@router.get(
    "/summary",
    response_model=DashboardSummary,
    status_code=status.HTTP_200_OK,
    summary="System-wide dashboard summary",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient role"},
        500: {"description": "Database aggregation failure"},
    },
)
async def get_summary(
    _user: UserInDB = Depends(require_roles(UserRole.ADMIN, UserRole.DOCTOR)),
    svc: DashboardService = Depends(_svc),
) -> DashboardSummary:
    """
    Return high-level system-wide statistics for the dashboard home card.

    **Includes:**
    - `total_patients` — all patient records
    - `total_diagnoses` — all diagnosis records
    - `total_report_analyses` — report analyses performed (0 until persistence is added)
    - `high_risk_patients` — patients with ≥ 1 diagnosis confidence ≥ 80 %
    - `average_prediction_confidence` — mean AI confidence across all predictions
    - `pending_diagnoses` — awaiting AI analysis
    - `ai_reviewed_diagnoses` — AI complete, awaiting doctor review
    - `doctor_reviewed_diagnoses` — fully reviewed

    **Role required:** Admin · Doctor
    """
    try:
        return await svc.get_summary()
    except Exception as exc:
        logger.exception("Failed to compute dashboard summary: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute dashboard summary: {exc}",
        )


# ---------------------------------------------------------------------------
# GET /disease-distribution
# ---------------------------------------------------------------------------

@router.get(
    "/disease-distribution",
    response_model=DiseaseDistribution,
    status_code=status.HTTP_200_OK,
    summary="Disease prediction distribution",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient role"},
        500: {"description": "Database aggregation failure"},
    },
)
async def get_disease_distribution(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of diseases to return, ordered by count descending.",
    ),
    _user: UserInDB = Depends(require_roles(UserRole.ADMIN, UserRole.DOCTOR)),
    svc: DashboardService = Depends(_svc),
) -> DiseaseDistribution:
    """
    Return per-disease prediction counts for chart rendering.

    Only diagnoses with a non-null `predicted_disease` are counted.
    Results are sorted by count descending so the most predicted diseases
    appear first.

    Suitable for driving:
    - Bar charts (disease vs count)
    - Pie / donut charts (disease frequency)
    - League-table components

    **Role required:** Admin · Doctor
    """
    try:
        return await svc.get_disease_distribution(limit=limit)
    except Exception as exc:
        logger.exception("Failed to compute disease distribution: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute disease distribution: {exc}",
        )


# ---------------------------------------------------------------------------
# GET /monthly-analytics
# ---------------------------------------------------------------------------

@router.get(
    "/monthly-analytics",
    response_model=MonthlyAnalytics,
    status_code=status.HTTP_200_OK,
    summary="Monthly trend analytics",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient role"},
        500: {"description": "Database aggregation failure"},
    },
)
async def get_monthly_analytics(
    months: int = Query(
        default=12,
        ge=1,
        le=36,
        description="Number of recent calendar months to return (1–36, default 12).",
    ),
    _user: UserInDB = Depends(require_roles(UserRole.ADMIN, UserRole.DOCTOR)),
    svc: DashboardService = Depends(_svc),
) -> MonthlyAnalytics:
    """
    Return monthly counts for patients, diagnoses, and report analyses.

    Data points are ordered **oldest-first** so they can be passed directly
    to time-series chart libraries without client-side sorting.

    Each data point contains:
    - `year` and `month` — numeric calendar identifiers
    - `month_label` — formatted string (e.g. `"Jul 2026"`) for chart axis labels
    - `new_patients` — patients created in that month
    - `new_diagnoses` — diagnoses created in that month
    - `report_analyses` — always 0 until report analyses are persisted

    Months with zero activity are **not** included — only months that have
    at least one patient or diagnosis record are returned.

    **Role required:** Admin · Doctor
    """
    try:
        return await svc.get_monthly_analytics(months=months)
    except Exception as exc:
        logger.exception("Failed to compute monthly analytics: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute monthly analytics: {exc}",
        )


# ---------------------------------------------------------------------------
# GET /model-performance
# ---------------------------------------------------------------------------

@router.get(
    "/model-performance",
    response_model=ModelPerformance,
    status_code=status.HTTP_200_OK,
    summary="ML model identity and evaluation metrics",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient role"},
        500: {"description": "Metric computation failure"},
    },
)
async def get_model_performance(
    _user: UserInDB = Depends(require_roles(UserRole.ADMIN, UserRole.DOCTOR)),
    svc: DashboardService = Depends(_svc),
) -> ModelPerformance:
    """
    Return current ML model identity and evaluation metrics.

    Metrics are computed against the held-out test split that was used during
    training (80/20 stratified split, `random_state=42`) and **cached for the
    process lifetime** — evaluation does not re-run on every HTTP request.

    **Metrics returned:**
    - `model_name` — scikit-learn class name (e.g. `RandomForestClassifier`)
    - `model_version` — pipeline semver string
    - `disease_classes` — number of unique disease labels
    - `accuracy` — fraction of test samples correctly classified
    - `precision` — weighted-average precision across all classes
    - `recall` — weighted-average recall across all classes
    - `f1_score` — weighted-average F1-score across all classes

    When model artefacts are missing (e.g. first deploy before training),
    `metrics_available` will be `false` and `metrics_note` will explain why.

    **Role required:** Admin · Doctor
    """
    try:
        return await svc.get_model_performance()
    except Exception as exc:
        logger.exception("Failed to retrieve model performance: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve model performance: {exc}",
        )