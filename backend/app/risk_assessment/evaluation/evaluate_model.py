from __future__ import annotations

"""Model evaluation utilities for the Risk Assessment module.

This module provides a reusable :class:`ModelEvaluator` class that
evaluates an already-trained model against a held-out test set,
computing standard classification metrics, a confusion matrix, and a
classification report. Results are returned as dictionaries and can be
saved as a JSON evaluation report. This module performs no plotting, no
model comparison, and no retraining.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None  # type: ignore[assignment]

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None  # type: ignore[assignment]

try:
    from sklearn.metrics import (
        accuracy_score,
        classification_report,
        confusion_matrix,
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
    )
except ImportError:  # pragma: no cover
    accuracy_score = None
    classification_report = None
    confusion_matrix = None
    f1_score = None
    precision_score = None
    recall_score = None
    roc_auc_score = None

try:
    from app.risk_assessment.utils.file_utils import create_directory
    from app.risk_assessment.utils.logging_utils import get_logger
except ImportError:  # pragma: no cover
    try:
        from backend.app.risk_assessment.utils.file_utils import create_directory
        from backend.app.risk_assessment.utils.logging_utils import get_logger
    except ImportError:  # pragma: no cover
        from risk_assessment.utils.file_utils import create_directory
        from risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)


class ModelEvaluator:
    """Evaluate a trained classification model on a held-out test set.

    This class is disease-agnostic and model-agnostic: it operates on
    any already-trained scikit-learn-compatible classifier (including
    XGBoost and MLP models) together with a test feature matrix and
    target vector. It does not train, retrain, or compare models, and it
    generates no plots.

    Attributes:
        model: The trained model instance to evaluate.
        x_test: Test feature matrix.
        y_test: Test target vector.
        model_name: Optional descriptive name for the model, used in
            logging and report metadata.
    """

    def __init__(
        self,
        model: Any,
        x_test: Union[pd.DataFrame, np.ndarray],
        y_test: Union[pd.Series, np.ndarray],
        model_name: Optional[str] = None,
    ) -> None:
        """Initialize the ModelEvaluator.

        Args:
            model: A trained model exposing a ``predict`` method (and
                optionally ``predict_proba`` or ``decision_function`` for
                ROC-AUC computation).
            x_test: Test feature matrix.
            y_test: Test target vector (ground truth labels).
            model_name: Optional descriptive name for the model (e.g.,
                ``"random_forest"``), used in logging and report
                metadata. Defaults to the model's class name if not
                provided.

        Raises:
            ValueError: If ``model`` does not expose a ``predict``
                method.
        """
        if not hasattr(model, "predict"):
            error_message = "The provided model does not implement a 'predict' method."
            logger.error(error_message)
            raise ValueError(error_message)

        self.model: Any = model
        self.x_test: Union[pd.DataFrame, np.ndarray] = x_test
        self.y_test: Union[pd.Series, np.ndarray] = y_test
        self.model_name: str = model_name or type(model).__name__

    def _get_predictions(self) -> np.ndarray:
        """Generate predicted labels for the test set.

        Returns:
            numpy.ndarray: Predicted class labels.

        Raises:
            Exception: Re-raises any exception encountered while
                generating predictions, after logging it.
        """
        try:
            predictions = self.model.predict(self.x_test)
            logger.info("Generated predictions for model '%s'.", self.model_name)
            return predictions
        except Exception as error:
            logger.error("Failed to generate predictions for '%s': %s", self.model_name, error)
            raise

    def _get_prediction_scores(self) -> Optional[np.ndarray]:
        """Generate prediction scores or probabilities for ROC-AUC computation.

        Attempts to use ``predict_proba`` first (taking the probability
        of the positive class), then falls back to ``decision_function``
        if available.

        Returns:
            Optional[numpy.ndarray]: An array of continuous scores
            suitable for ROC-AUC computation, or ``None`` if the model
            supports neither ``predict_proba`` nor ``decision_function``.
        """
        try:
            if hasattr(self.model, "predict_proba"):
                probabilities = self.model.predict_proba(self.x_test)
                return probabilities[:, 1]
            if hasattr(self.model, "decision_function"):
                return self.model.decision_function(self.x_test)

            logger.warning(
                "Model '%s' supports neither 'predict_proba' nor 'decision_function'; "
                "ROC-AUC cannot be computed.",
                self.model_name,
            )
            return None
        except Exception as error:
            logger.warning(
                "Failed to compute prediction scores for '%s': %s", self.model_name, error
            )
            return None

    def calculate_accuracy(self, predictions: np.ndarray) -> float:
        """Calculate accuracy score.

        Args:
            predictions: Predicted class labels.

        Returns:
            float: The accuracy score.
        """
        score = float(accuracy_score(self.y_test, predictions))
        logger.info("Accuracy for '%s': %.4f", self.model_name, score)
        return score

    def calculate_precision(self, predictions: np.ndarray) -> float:
        """Calculate precision score (weighted average for multi-class support).

        Args:
            predictions: Predicted class labels.

        Returns:
            float: The precision score.
        """
        score = float(precision_score(self.y_test, predictions, average="weighted", zero_division=0))
        logger.info("Precision for '%s': %.4f", self.model_name, score)
        return score

    def calculate_recall(self, predictions: np.ndarray) -> float:
        """Calculate recall score (weighted average for multi-class support).

        Args:
            predictions: Predicted class labels.

        Returns:
            float: The recall score.
        """
        score = float(recall_score(self.y_test, predictions, average="weighted", zero_division=0))
        logger.info("Recall for '%s': %.4f", self.model_name, score)
        return score

    def calculate_f1_score(self, predictions: np.ndarray) -> float:
        """Calculate F1 score (weighted average for multi-class support).

        Args:
            predictions: Predicted class labels.

        Returns:
            float: The F1 score.
        """
        score = float(f1_score(self.y_test, predictions, average="weighted", zero_division=0))
        logger.info("F1 score for '%s': %.4f", self.model_name, score)
        return score

    def calculate_roc_auc(self, scores: Optional[np.ndarray]) -> Optional[float]:
        """Calculate ROC-AUC score.

        Args:
            scores: Continuous prediction scores or probabilities for the
                positive class. If ``None``, ROC-AUC cannot be computed.

        Returns:
            Optional[float]: The ROC-AUC score, or ``None`` if it could
            not be computed (e.g., missing scores or a single-class
            target).
        """
        if scores is None:
            return None

        try:
            score = float(roc_auc_score(self.y_test, scores))
            logger.info("ROC-AUC for '%s': %.4f", self.model_name, score)
            return score
        except ValueError as error:
            logger.warning("Could not compute ROC-AUC for '%s': %s", self.model_name, error)
            return None

    def generate_confusion_matrix(self, predictions: np.ndarray) -> Dict[str, Any]:
        """Generate a confusion matrix.

        Args:
            predictions: Predicted class labels.

        Returns:
            Dict[str, Any]: A dictionary with keys ``"matrix"`` (the
            confusion matrix as a nested list) and ``"labels"`` (the
            sorted class labels used to construct the matrix).
        """
        labels = sorted(pd.Series(self.y_test).unique().tolist())
        matrix = confusion_matrix(self.y_test, predictions, labels=labels)

        result = {"matrix": matrix.tolist(), "labels": labels}
        logger.info("Confusion matrix generated for '%s'.", self.model_name)
        return result

    def generate_classification_report(self, predictions: np.ndarray) -> Dict[str, Any]:
        """Generate a classification report.

        Args:
            predictions: Predicted class labels.

        Returns:
            Dict[str, Any]: The classification report as a nested
            dictionary (per-class precision, recall, F1, and support).
        """
        report = classification_report(self.y_test, predictions, output_dict=True, zero_division=0)
        logger.info("Classification report generated for '%s'.", self.model_name)
        return report

    def evaluate(self) -> Dict[str, Any]:
        """Run the full evaluation and compile all metrics into a report.

        Returns:
            Dict[str, Any]: A dictionary with keys ``"model_name"``,
            ``"accuracy"``, ``"precision"``, ``"recall"``, ``"f1_score"``,
            ``"roc_auc"``, ``"confusion_matrix"``,
            ``"classification_report"``.

        Raises:
            Exception: Re-raises any exception encountered during
                evaluation, after logging it.
        """
        try:
            logger.info("Starting evaluation for model '%s'.", self.model_name)

            predictions = self._get_predictions()
            scores = self._get_prediction_scores()

            report: Dict[str, Any] = {
                "model_name": self.model_name,
                "accuracy": self.calculate_accuracy(predictions),
                "precision": self.calculate_precision(predictions),
                "recall": self.calculate_recall(predictions),
                "f1_score": self.calculate_f1_score(predictions),
                "roc_auc": self.calculate_roc_auc(scores),
                "confusion_matrix": self.generate_confusion_matrix(predictions),
                "classification_report": self.generate_classification_report(predictions),
            }

            logger.info("Evaluation completed for model '%s'.", self.model_name)
            return report
        except Exception as error:
            logger.error("Evaluation failed for model '%s': %s", self.model_name, error)
            raise

    def save_report_as_json(
        self, report: Dict[str, Any], output_path: Union[str, Path]
    ) -> Path:
        """Save an evaluation report dictionary to a JSON file.

        Args:
            report: The evaluation report dictionary to save (typically
                the output of :meth:`evaluate`).
            output_path: Destination path for the JSON file.

        Returns:
            Path: The resolved path where the report was saved.

        Raises:
            OSError: If the file cannot be written due to filesystem
                permission issues.
            TypeError: If the report contains values that are not
                JSON-serializable.
        """
        path = Path(output_path)

        try:
            create_directory(path.parent)
            with open(path, "w", encoding="utf-8") as json_file:
                json.dump(report, json_file, indent=4)

            logger.info("Evaluation report saved to: %s", path.resolve())
            return path
        except (OSError, TypeError) as error:
            logger.error("Failed to save evaluation report to '%s': %s", path, error)
            raise