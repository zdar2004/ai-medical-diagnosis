"""
metrics.py
==========

Reusable evaluation metrics for binary classification models.

This module provides a generic EvaluationMetrics class capable of
calculating common binary-classification metrics for any disease model.

Responsibilities
----------------
- Accuracy
- Precision
- Recall
- F1 Score
- ROC-AUC
- Confusion Matrix
- Classification Report

This module NEVER:

- loads datasets
- loads models
- performs predictions
- saves files
- generates plots

It only computes evaluation metrics.
"""

from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)


class EvaluationMetrics:
    """
    Generic binary-classification evaluation utility.

    This class is completely model-agnostic and disease-agnostic.

    It accepts true labels, predicted labels, and optionally
    prediction probabilities, then calculates common evaluation metrics.

    Supported Metrics
    -----------------
    - Accuracy
    - Precision
    - Recall
    - F1 Score
    - ROC-AUC
    - Confusion Matrix
    - Classification Report

    Notes
    -----
    ROC-AUC is only computed when prediction probabilities
    are supplied.
    """

    def __init__(self) -> None:
        """Initialize EvaluationMetrics."""
        logger.info("EvaluationMetrics initialized.")

    # ------------------------------------------------------------------
    # Validation Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_inputs(
        y_true: List[int],
        y_pred: List[int],
    ) -> None:
        """
        Validate prediction inputs.

        Args:
            y_true:
                Ground-truth labels.

            y_pred:
                Predicted labels.

        Raises:
            ValueError:
                If inputs are invalid.
        """

        if y_true is None:
            raise ValueError("y_true cannot be None.")

        if y_pred is None:
            raise ValueError("y_pred cannot be None.")

        if len(y_true) == 0:
            raise ValueError("y_true cannot be empty.")

        if len(y_true) != len(y_pred):
            raise ValueError(
                "Length mismatch between y_true and y_pred."
            )

    @staticmethod
    def _validate_probability(
        y_probability: Optional[List[float]],
        expected_size: int,
    ) -> None:
        """
        Validate probability vector.

        Args:
            y_probability:
                Positive-class probabilities.

            expected_size:
                Expected vector size.

        Raises:
            ValueError
        """

        if y_probability is None:
            return

        if len(y_probability) != expected_size:
            raise ValueError(
                "Probability vector length does not match labels."
            )

    # ------------------------------------------------------------------
    # Accuracy
    # ------------------------------------------------------------------

    def accuracy(
        self,
        y_true: List[int],
        y_pred: List[int],
    ) -> float:
        """
        Calculate classification accuracy.

        Args:
            y_true:
                Ground-truth labels.

            y_pred:
                Predicted labels.

        Returns:
            Accuracy score.
        """

        self._validate_inputs(y_true, y_pred)

        score = float(
            accuracy_score(
                y_true,
                y_pred,
            )
        )

        logger.info(
            "Accuracy calculated: %.4f",
            score,
        )

        return score

    # ------------------------------------------------------------------
    # Precision
    # ------------------------------------------------------------------

    def precision(
        self,
        y_true: List[int],
        y_pred: List[int],
    ) -> float:
        """
        Calculate precision.

        Returns
        -------
        float
            Precision score.
        """

        self._validate_inputs(y_true, y_pred)

        score = float(
            precision_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        )

        logger.info(
            "Precision calculated: %.4f",
            score,
        )

        return score

    # ------------------------------------------------------------------
    # Recall
    # ------------------------------------------------------------------

    def recall(
        self,
        y_true: List[int],
        y_pred: List[int],
    ) -> float:
        """
        Calculate recall.

        Returns
        -------
        float
            Recall score.
        """

        self._validate_inputs(
            y_true,
            y_pred,
        )

        score = float(
            recall_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        )

        logger.info(
            "Recall calculated: %.4f",
            score,
        )

        return score

    # ------------------------------------------------------------------
    # F1
    # ------------------------------------------------------------------

    def f1(
        self,
        y_true: List[int],
        y_pred: List[int],
    ) -> float:
        """
        Calculate F1 Score.

        Returns
        -------
        float
            F1 score.
        """

        self._validate_inputs(
            y_true,
            y_pred,
        )

        score = float(
            f1_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        )

        logger.info(
            "F1 Score calculated: %.4f",
            score,
        )

        return score

    # ------------------------------------------------------------------
    # ROC-AUC
    # ------------------------------------------------------------------

    def roc_auc(
        self,
        y_true: List[int],
        y_probability: Optional[List[float]],
    ) -> Optional[float]:
        """
        Calculate ROC-AUC score.

        ROC-AUC is only computed when prediction probabilities are
        provided. If probabilities are unavailable, ``None`` is returned.

        Args:
            y_true:
                Ground-truth binary labels.

            y_probability:
                Probability estimates for the positive class.

        Returns:
            ROC-AUC score if probabilities are available,
            otherwise ``None``.
        """

        if y_probability is None:
            logger.warning(
                "ROC-AUC skipped because probability scores were not provided."
            )
            return None

        self._validate_probability(
            y_probability,
            len(y_true),
        )

        score = float(
            roc_auc_score(
                y_true,
                y_probability,
            )
        )

        logger.info(
            "ROC-AUC calculated: %.4f",
            score,
        )

        return score

    # ------------------------------------------------------------------
    # Confusion Matrix
    # ------------------------------------------------------------------

    def confusion_matrix(
        self,
        y_true: List[int],
        y_pred: List[int],
    ) -> List[List[int]]:
        """
        Compute confusion matrix.

        Args:
            y_true:
                Ground-truth labels.

            y_pred:
                Predicted labels.

        Returns:
            Nested Python list representation of the confusion matrix.
        """

        self._validate_inputs(
            y_true,
            y_pred,
        )

        matrix = confusion_matrix(
            y_true,
            y_pred,
        )

        result = matrix.tolist()

        logger.info(
            "Confusion matrix calculated."
        )

        return result

    # ------------------------------------------------------------------
    # Classification Report
    # ------------------------------------------------------------------

    def classification_report(
        self,
        y_true: List[int],
        y_pred: List[int],
    ) -> Dict[str, Any]:
        """
        Generate a classification report.

        Args:
            y_true:
                Ground-truth labels.

            y_pred:
                Predicted labels.

        Returns:
            Dictionary representation of the classification report.
        """

        self._validate_inputs(
            y_true,
            y_pred,
        )

        report = classification_report(
            y_true,
            y_pred,
            output_dict=True,
            zero_division=0,
        )

        logger.info(
            "Classification report generated."
        )

        return report

    # ------------------------------------------------------------------
    # Complete Evaluation
    # ------------------------------------------------------------------

    def evaluate(
        self,
        y_true: List[int],
        y_pred: List[int],
        y_probability: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """
        Compute all supported evaluation metrics.

        Args:
            y_true:
                Ground-truth labels.

            y_pred:
                Predicted labels.

            y_probability:
                Optional positive-class probabilities.

        Returns:
            Dictionary containing all evaluation metrics.
        """

        logger.info(
            "Starting model evaluation."
        )

        self._validate_inputs(
            y_true,
            y_pred,
        )

        self._validate_probability(
            y_probability,
            len(y_true),
        )

        metrics = {
            "accuracy": self.accuracy(
                y_true,
                y_pred,
            ),
            "precision": self.precision(
                y_true,
                y_pred,
            ),
            "recall": self.recall(
                y_true,
                y_pred,
            ),
            "f1_score": self.f1(
                y_true,
                y_pred,
            ),
            "roc_auc": self.roc_auc(
                y_true,
                y_probability,
            ),
            "confusion_matrix": self.confusion_matrix(
                y_true,
                y_pred,
            ),
            "classification_report": self.classification_report(
                y_true,
                y_pred,
            ),
        }

        logger.info(
            "Evaluation completed successfully."
        )

        return metrics