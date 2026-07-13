"""
Reusable evaluation engine for the Risk Assessment module.

This module evaluates trained machine-learning models on processed
datasets and produces standard binary-classification metrics.

Responsibilities
----------------
* Load trained models.
* Load processed datasets.
* Generate predictions.
* Compute evaluation metrics.
* Return structured evaluation reports.

The module intentionally contains no disease-specific logic.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import joblib
import pandas as pd

from app.risk_assessment.evaluation.metrics import EvaluationMetrics
from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)

DEFAULT_PROCESSED_DATASET_DIR = Path(
    "risk_assessment/datasets/processed"
)

DEFAULT_SAVED_MODELS_DIR = Path(
    "risk_assessment/saved_models"
)

class ModelEvaluator:
    """
    Evaluate trained binary-classification models.

    The evaluator is completely reusable and disease-independent.

    Expected directory structure
    ----------------------------

    processed/
        disease_name/
            X_test.csv
            y_test.csv

    saved_models/
        disease_name/
            disease_model.pkl
    """

    def __init__(
        self,
        processed_dataset_dir: Union[str, Path] = DEFAULT_PROCESSED_DATASET_DIR,
        saved_models_dir: Union[str, Path] = DEFAULT_SAVED_MODELS_DIR,
    ) -> None:
        """
        Initialize evaluator.

        Args:
            processed_dataset_dir:
                Directory containing processed datasets.

            saved_models_dir:
                Directory containing trained models.
        """

        self.processed_dataset_dir = Path(processed_dataset_dir)
        self.saved_models_dir = Path(saved_models_dir)

        self.metrics = EvaluationMetrics()

    def _resolve_model_path(
        self,
        disease_name: str,
        model_name: str,
    ) -> Path:
        """
        Resolve trained model path.

        Args:
            disease_name:
                Disease identifier.

            model_name:
                Model identifier.

        Returns:
            Path to model.

        Raises:
            FileNotFoundError
        """

        model_path = (
            self.saved_models_dir
            / disease_name
            / f"{disease_name}_{model_name}.pkl"
        )

        if not model_path.exists():
            raise FileNotFoundError(
                f"Model not found: {model_path}"
            )

        logger.info("Resolved model path: %s", model_path)

        return model_path
    
    def _resolve_dataset_paths(
        self,
        disease_name: str,
    ) -> Dict[str, Path]:
        """
        Resolve processed dataset paths.

        Returns
        -------
        Dictionary containing:

        - X_test
        - y_test
        """

        dataset_dir = (
            self.processed_dataset_dir
            / disease_name
        )

        x_test = dataset_dir / "X_test.csv"
        y_test = dataset_dir / "y_test.csv"

        if not x_test.exists():
            raise FileNotFoundError(x_test)

        if not y_test.exists():
            raise FileNotFoundError(y_test)

        logger.info(
            "Resolved processed datasets for '%s'.",
            disease_name,
        )

        return {
            "X_test": x_test,
            "y_test": y_test,
        }
    
    def _load_model(
        self,
        disease_name: str,
        model_name: str,
    ) -> Any:
        """
        Load trained model.

        Returns
        -------
        Loaded sklearn model.
        """

        model_path = self._resolve_model_path(
            disease_name,
            model_name,
        )

        model = joblib.load(model_path)

        logger.info(
            "Loaded model '%s'.",
            type(model).__name__,
        )

        return model
    
    def _load_processed_data(
        self,
        disease_name: str,
    ) -> Dict[str, Union[pd.DataFrame, pd.Series]]:
        """
        Load processed evaluation datasets.

        Args:
            disease_name:
                Disease identifier.

        Returns:
            Dictionary containing:

            - X_test
            - y_test
        """

        dataset_paths = self._resolve_dataset_paths(
            disease_name,
        )

        x_test = pd.read_csv(
            dataset_paths["X_test"],
        )

        y_test = pd.read_csv(
            dataset_paths["y_test"],
        ).iloc[:, 0]

        logger.info(
            "Loaded processed datasets for '%s'. "
            "X_test=%s, y_test=%s",
            disease_name,
            x_test.shape,
            y_test.shape,
        )

        return {
            "X_test": x_test,
            "y_test": y_test,
        }
    
    def _predict(
        self,
        model: Any,
        x_test: pd.DataFrame,
    ) -> pd.Series:
        """
        Generate class predictions.

        Args:
            model:
                Loaded sklearn model.

            x_test:
                Processed testing features.

        Returns:
            Predicted labels.
        """

        predictions = model.predict(x_test)

        logger.info(
            "Generated %d predictions.",
            len(predictions),
        )

        return pd.Series(
            predictions,
            index=x_test.index,
        )
    
    def _predict_probabilities(
        self,
        model: Any,
        x_test: pd.DataFrame,
    ) -> Optional[pd.Series]:
        """
        Generate positive-class probabilities.

        Returns
        -------
        pd.Series
            Positive-class probabilities.

        None
            If the model does not support predict_proba().
        """

        if not hasattr(model, "predict_proba"):
            logger.warning(
                "Model '%s' does not support "
                "predict_proba().",
                type(model).__name__,
            )
            return None

        probabilities = model.predict_proba(x_test)

        positive_probability = pd.Series(
            probabilities[:, 1],
            index=x_test.index,
        )

        logger.info(
            "Generated probability scores."
        )

        return positive_probability
    
    def _collect_predictions(
        self,
        disease_name: str,
        model_name: str,
    ) -> Dict[str, Any]:
        """
        Load model, load processed data, and generate predictions.

        Args:
            disease_name:
                Disease identifier.

            model_name:
                Trained model identifier.

        Returns:
            Dictionary containing:

            - model
            - X_test
            - y_test
            - predictions
            - probabilities
        """

        model = self._load_model(
            disease_name,
            model_name,
        )

        datasets = self._load_processed_data(
            disease_name,
        )

        predictions = self._predict(
            model,
            datasets["X_test"],
        )

        probabilities = self._predict_probabilities(
            model,
            datasets["X_test"],
        )

        return {
            "model": model,
            "X_test": datasets["X_test"],
            "y_test": datasets["y_test"],
            "predictions": predictions,
            "probabilities": probabilities,
        }
    
    def evaluate(
        self,
        disease_name: str,
        model_name: str,
    ) -> Dict[str, Any]:
        """
        Evaluate a trained model using the processed test dataset.

        This method performs the complete evaluation workflow:

        1. Load the trained model.
        2. Load the processed test dataset.
        3. Generate predictions.
        4. Generate probability scores (when supported).
        5. Compute evaluation metrics.
        6. Return a structured evaluation report.

        Args:
            disease_name:
                Disease identifier.

            model_name:
                Model identifier.

        Returns:
            Dictionary containing:

            - disease_name
            - model_name
            - model_type
            - test_samples
            - metrics
            - evaluated_at

        Raises:
            FileNotFoundError:
                If the model or processed dataset is missing.

            Exception:
                Re-raises unexpected evaluation errors after logging.
        """
        try:
            logger.info(
                "Starting evaluation for disease='%s', model='%s'.",
                disease_name,
                model_name,
            )

            prediction_bundle = self._collect_predictions(
                disease_name=disease_name,
                model_name=model_name,
            )

            metrics = self.metrics.evaluate(
                y_true=prediction_bundle["y_test"],
                y_pred=prediction_bundle["predictions"],
                y_probability=prediction_bundle["probabilities"],
            )

            report = {
                "disease_name": disease_name,
                "model_name": model_name,
                "model_type": type(
                    prediction_bundle["model"]
                ).__name__,
                "test_samples": int(
                    len(prediction_bundle["y_test"])
                ),
                "metrics": metrics,
                "evaluated_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            }

            logger.info(
                "Evaluation completed successfully for "
                "disease='%s', model='%s'.",
                disease_name,
                model_name,
            )

            return report

        except Exception as error:
            logger.exception(
                "Model evaluation failed for disease='%s', "
                "model='%s': %s",
                disease_name,
                model_name,
                error,
            )
            raise

        

    