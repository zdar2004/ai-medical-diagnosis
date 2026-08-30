"""dashboard_service.py
========================
Service layer for the MediSys Dashboard Analytics API.

All read operations are executed as MongoDB aggregation pipelines via Motor,
so the database does the heavy lifting — no Python-side counting loops.

Model performance metrics are computed once per process lifetime via
:func:`~app.ai.evaluation.evaluate_model.evaluate` and cached at module
level.  This prevents re-running the sklearn evaluation on every HTTP
request, which would be prohibitively slow.
"""

import logging
from pathlib import Path
import joblib
from calendar import month_abbr
from datetime import datetime, timezone
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.dashboard import (
    DashboardSummary,
    DiseaseCount,
    DiseaseDistribution,
    ModelMetric,
    ModelPerformance,
    MonthlyAnalytics,
    MonthlyDataPoint,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Confidence threshold above which a patient is considered high-risk.
HIGH_RISK_CONFIDENCE_THRESHOLD: float = 0.80

# Pipeline version — bump when metrics or queries change.
_DASHBOARD_VERSION: str = "1.0.0"

# ---------------------------------------------------------------------------
# Module-level model metrics cache
# ---------------------------------------------------------------------------
# Computed once on first request that needs it; reused for all subsequent
# requests in the same process lifetime.  None means "not yet computed".

_MODEL_METRICS_CACHE: Optional[ModelPerformance] = None


def _load_model_metrics() -> ModelPerformance:
    """Load saved multi-model training performance metrics."""

    global _MODEL_METRICS_CACHE

    if _MODEL_METRICS_CACHE is not None:
        logger.debug("Returning cached model metrics.")
        return _MODEL_METRICS_CACHE

    logger.info("Loading saved multi-model performance metrics.")

    try:
        backend_dir = Path(__file__).resolve().parents[2]

        performance_path = (
            backend_dir
            / "app"
            / "ai"
            / "models"
            / "model_performance.pkl"
        )

        if not performance_path.exists():
            raise FileNotFoundError(
                f"Performance file not found: {performance_path}"
            )

        performance_data = joblib.load(performance_path)

        results = [
            ModelMetric(
                model=item["model"],
                accuracy=round(item["accuracy"], 4),
                precision=round(item["precision"], 4),
                recall=round(item["recall"], 4),
                f1_score=round(item["f1_score"], 4),
            )
            for item in performance_data.get("results", [])
        ]

        _MODEL_METRICS_CACHE = ModelPerformance(
            best_model=performance_data.get(
                "best_model",
                "Unknown",
            ),
            disease_classes=performance_data.get(
                "disease_classes",
                0,
            ),
            total_samples=performance_data.get(
                "total_samples",
                0,
            ),
            training_samples=performance_data.get(
                "training_samples",
                0,
            ),
            testing_samples=performance_data.get(
                "testing_samples",
                0,
            ),
            results=results,
            metrics_available=True,
            metrics_note=None,
        )

        logger.info(
            "Loaded performance metrics for %d models. Best model: %s",
            len(results),
            _MODEL_METRICS_CACHE.best_model,
        )

    except FileNotFoundError as exc:
        logger.warning(
            "Model performance file not found: %s",
            exc,
        )

        _MODEL_METRICS_CACHE = ModelPerformance(
            best_model="Unknown",
            disease_classes=0,
            total_samples=0,
            training_samples=0,
            testing_samples=0,
            results=[],
            metrics_available=False,
            metrics_note=(
                "Training performance metrics not found. "
                "Run the model training pipeline first."
            ),
        )

    except Exception as exc:
        logger.exception(
            "Unexpected error loading model performance: %s",
            exc,
        )

        _MODEL_METRICS_CACHE = ModelPerformance(
            best_model="Unknown",
            disease_classes=0,
            total_samples=0,
            training_samples=0,
            testing_samples=0,
            results=[],
            metrics_available=False,
            metrics_note=f"Metrics unavailable: {exc}",
        )

    return _MODEL_METRICS_CACHE

# ---------------------------------------------------------------------------
# DashboardService
# ---------------------------------------------------------------------------

class DashboardService:
    """Async service that queries MongoDB for dashboard analytics.

    Follows the same constructor pattern as :class:`~services.patient_service.PatientService`
    and :class:`~services.diagnosis_service.DiagnosisService`.

    Args:
        db: Live :class:`~motor.motor_asyncio.AsyncIOMotorDatabase` handle
            injected by FastAPI's dependency system.
    """

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db         = db
        self.patients   = db["patients"]
        self.diagnoses  = db["diagnoses"]

    # ── Summary ───────────────────────────────────────────────────────────────

    async def get_summary(self) -> DashboardSummary:
        """Return high-level system-wide statistics.

        Runs four concurrent MongoDB operations:

        * ``count_documents`` on patients
        * ``count_documents`` on diagnoses
        * Aggregation for status breakdown and confidence average
        * Aggregation for high-risk patient count

        Returns:
            :class:`~models.dashboard.DashboardSummary`
        """
        logger.info("Computing dashboard summary.")

        # ── Basic counts ──────────────────────────────────────────────────────
        total_patients  = await self.patients.count_documents({})
        total_diagnoses = await self.diagnoses.count_documents({})

        # ── Status breakdown + confidence average (single pipeline) ───────────
        status_pipeline = [
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "avg_conf": {
                        "$avg": {
                            "$cond": [
                                {"$gt": ["$confidence_score", None]},
                                "$confidence_score",
                                None,
                            ]
                        }
                    },
                }
            }
        ]
        status_cursor = self.diagnoses.aggregate(status_pipeline)
        status_docs   = await status_cursor.to_list(length=10)

        pending           = 0
        ai_reviewed       = 0
        doctor_reviewed   = 0
        total_conf        = 0.0
        conf_count        = 0

        for doc in status_docs:
            s = doc.get("_id", "")
            c = doc.get("count", 0)
            if s == "pending":
                pending = c
            elif s == "ai_reviewed":
                ai_reviewed = c
            elif s == "doctor_reviewed":
                doctor_reviewed = c
            avg = doc.get("avg_conf")
            if avg is not None:
                total_conf += avg * c
                conf_count += c

        avg_confidence: Optional[float] = (
            round(total_conf / conf_count, 4) if conf_count > 0 else None
        )

        # ── High-risk patients ────────────────────────────────────────────────
        # A patient is high-risk if at least one of their diagnoses has a
        # confidence score >= HIGH_RISK_CONFIDENCE_THRESHOLD.
        high_risk_pipeline = [
            {
                "$match": {
                    "confidence_score": {
                        "$gte": HIGH_RISK_CONFIDENCE_THRESHOLD
                    }
                }
            },
            {
                "$group": {
                    "_id": "$patient_id"
                }
            },
            {
                "$count": "total"
            },
        ]
        hr_cursor = self.diagnoses.aggregate(high_risk_pipeline)
        hr_docs   = await hr_cursor.to_list(length=1)
        high_risk = hr_docs[0]["total"] if hr_docs else 0

        logger.info(
            "Summary computed: patients=%d  diagnoses=%d  high_risk=%d  avg_conf=%s",
            total_patients, total_diagnoses, high_risk, avg_confidence,
        )

        return DashboardSummary(
            total_patients=total_patients,
            total_diagnoses=total_diagnoses,
            total_report_analyses=0,   # Not yet persisted — Phase N
            high_risk_patients=high_risk,
            average_prediction_confidence=avg_confidence,
            pending_diagnoses=pending,
            ai_reviewed_diagnoses=ai_reviewed,
            doctor_reviewed_diagnoses=doctor_reviewed,
        )

    # ── Disease distribution ──────────────────────────────────────────────────

    async def get_disease_distribution(
        self,
        limit: int = 20,
    ) -> DiseaseDistribution:
        """Return per-disease prediction counts for chart rendering.

        Only diagnoses that have a non-null ``predicted_disease`` are included.
        Results are sorted by count descending.

        Args:
            limit: Maximum number of diseases to return (default 20).

        Returns:
            :class:`~models.dashboard.DiseaseDistribution`
        """
        logger.info("Computing disease distribution (limit=%d).", limit)

        pipeline = [
            {
                "$match": {
                    "predicted_disease": {"$ne": None}
                }
            },
            {
                "$group": {
                    "_id": "$predicted_disease",
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": limit},
        ]

        cursor = self.diagnoses.aggregate(pipeline)
        docs   = await cursor.to_list(length=limit)

        distribution = [
            DiseaseCount(disease=doc["_id"], count=doc["count"])
            for doc in docs
            if doc.get("_id")
        ]

        total = sum(d.count for d in distribution)

        logger.info("Disease distribution: %d diseases, %d total.", len(distribution), total)

        return DiseaseDistribution(total=total, distribution=distribution)

    # ── Monthly analytics ─────────────────────────────────────────────────────

    async def get_monthly_analytics(
        self,
        months: int = 12,
    ) -> MonthlyAnalytics:
        """Return monthly new-patient and new-diagnosis counts.

        Args:
            months: How many recent calendar months to return (default 12).

        Returns:
            :class:`~models.dashboard.MonthlyAnalytics` with data points
            ordered oldest-first for chart rendering.
        """
        logger.info("Computing monthly analytics (months=%d).", months)

        # MongoDB $dateToString extracts "YYYY-MM" for grouping.
        def _monthly_pipeline(collection_field: str = "created_at") -> list:
            return [
                {
                    "$group": {
                        "_id": {
                            "year":  {"$year":  f"${collection_field}"},
                            "month": {"$month": f"${collection_field}"},
                        },
                        "count": {"$sum": 1},
                    }
                },
                {"$sort": {"_id.year": -1, "_id.month": -1}},
                {"$limit": months},
            ]

        patient_cursor   = self.patients.aggregate(_monthly_pipeline())
        diagnosis_cursor = self.diagnoses.aggregate(_monthly_pipeline())

        patient_docs   = await patient_cursor.to_list(length=months)
        diagnosis_docs = await diagnosis_cursor.to_list(length=months)

        # Build lookup dicts keyed by (year, month)
        patient_map   = {
            (d["_id"]["year"], d["_id"]["month"]): d["count"]
            for d in patient_docs
        }
        diagnosis_map = {
            (d["_id"]["year"], d["_id"]["month"]): d["count"]
            for d in diagnosis_docs
        }

        # Collect all unique (year, month) keys and sort oldest-first
        all_keys = sorted(
            set(patient_map.keys()) | set(diagnosis_map.keys()),
            key=lambda k: (k[0], k[1]),
        )

        data_points = [
            MonthlyDataPoint(
                year=year,
                month=month,
                month_label=f"{month_abbr[month]} {year}",
                new_patients=patient_map.get((year, month), 0),
                new_diagnoses=diagnosis_map.get((year, month), 0),
                report_analyses=0,   # Not yet persisted — Phase N
            )
            for year, month in all_keys
        ]

        logger.info("Monthly analytics: %d months of data returned.", len(data_points))

        return MonthlyAnalytics(
            months_returned=len(data_points),
            data=data_points,
        )

    # ── Model performance ─────────────────────────────────────────────────────

    async def get_model_performance(self) -> ModelPerformance:
        """Return current ML model identity and cached evaluation metrics.

        Delegates to the module-level :func:`_load_model_metrics` function
        which runs the sklearn evaluation once and caches the result.

        Returns:
            :class:`~models.dashboard.ModelPerformance`
        """
        logger.info("Fetching model performance metrics.")
        return _load_model_metrics()