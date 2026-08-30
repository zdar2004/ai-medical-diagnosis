from pathlib import Path

import joblib
from fastapi import APIRouter, HTTPException


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


_THIS_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _THIS_DIR.parents[3]

PERFORMANCE_PATH = (
    _BACKEND_DIR
    / "app"
    / "ai"
    / "models"
    / "model_performance.pkl"
)


@router.get("/model-performance")
def get_model_performance():

    if not PERFORMANCE_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Model performance data not found. "
                "Run the training pipeline first."
            ),
        )

    try:
        performance_data = joblib.load(
            PERFORMANCE_PATH
        )

        return {
            "best_model": performance_data["best_model"],
            "results": performance_data["results"],
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load model performance data: {str(exc)}",
        )