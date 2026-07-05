"""Model comparison utilities for the Risk Assessment module.

This module provides a reusable :class:`ModelComparison` class that
compares evaluation results (produced by :class:`ModelEvaluator`) across
multiple trained models, builds a comparison table, ranks models by a
configurable metric, and selects the best-performing model. This module
performs no plotting, training, or evaluation of its own; it strictly
consumes pre-computed evaluation reports.
"""

from typing import Any, Dict, List, Optional

import pandas as pd

from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)

SUPPORTED_METRICS = {"accuracy", "precision", "recall", "f1", "roc_auc"}

# Maps the public metric names used for selection/ranking to the key
# names produced by ModelEvaluator.evaluate().
METRIC_KEY_MAP = {
    "accuracy": "accuracy",
    "precision": "precision",
    "recall": "recall",
    "f1": "f1_score",
    "roc_auc": "roc_auc",
}


class ModelComparison:
    """Compare evaluation results across multiple trained models.

    This class consumes a collection of evaluation reports (one per
    model, typically produced by ``ModelEvaluator.evaluate()``) and
    provides comparison, ranking, and best-model selection utilities. It
    performs no training, evaluation, or plotting of its own, and
    contains no disease-specific logic.

    Supported model names are descriptive labels only (e.g.,
    ``"logistic_regression"``, ``"random_forest"``, ``"svm"``,
    ``"xgboost"``, ``"neural_network"``); any string label supplied by
    the caller is accepted.

    Attributes:
        evaluation_results: A mapping of model name to its evaluation
            report dictionary.
    """

    def __init__(self, evaluation_results: Dict[str, Dict[str, Any]]) -> None:
        """Initialize the ModelComparison.

        Args:
            evaluation_results: A dictionary mapping model name (e.g.,
                ``"random_forest"``) to its evaluation report dictionary,
                as produced by ``ModelEvaluator.evaluate()``. Each report
                is expected to contain at least the keys ``"accuracy"``,
                ``"precision"``, ``"recall"``, ``"f1_score"``, and
                ``"roc_auc"``.

        Raises:
            ValueError: If ``evaluation_results`` is empty or not a
                dictionary.
        """
        if not isinstance(evaluation_results, dict) or not evaluation_results:
            error_message = "evaluation_results must be a non-empty dictionary of model reports."
            logger.error(error_message)
            raise ValueError(error_message)

        self.evaluation_results: Dict[str, Dict[str, Any]] = evaluation_results

    def build_comparison_table(self) -> pd.DataFrame:
        """Build a comparison table of key metrics across all models.

        Returns:
            pd.DataFrame: A DataFrame indexed by model name, with columns
            ``"accuracy"``, ``"precision"``, ``"recall"``, ``"f1_score"``,
            and ``"roc_auc"``.

        Raises:
            Exception: Re-raises any exception encountered while building
                the table, after logging it.
        """
        try:
            rows = []
            for model_name, report in self.evaluation_results.items():
                rows.append(
                    {
                        "model_name": model_name,
                        "accuracy": report.get("accuracy"),
                        "precision": report.get("precision"),
                        "recall": report.get("recall"),
                        "f1_score": report.get("f1_score"),
                        "roc_auc": report.get("roc_auc"),
                    }
                )

            comparison_table = pd.DataFrame(rows).set_index("model_name")
            logger.info("Comparison table built for models: %s", list(self.evaluation_results.keys()))
            return comparison_table
        except Exception as error:
            logger.error("Failed to build comparison table: %s", error)
            raise

    def _resolve_metric_key(self, metric: str) -> str:
        """Validate and resolve a public metric name to its report key.

        Args:
            metric: Public metric name (e.g., ``"f1"``).

        Returns:
            str: The corresponding key used within evaluation report
            dictionaries (e.g., ``"f1_score"``).

        Raises:
            ValueError: If ``metric`` is not one of the supported metric
                names.
        """
        normalized_metric = metric.strip().lower()

        if normalized_metric not in SUPPORTED_METRICS:
            error_message = (
                f"Unsupported metric '{metric}'. Supported metrics are: {sorted(SUPPORTED_METRICS)}."
            )
            logger.error(error_message)
            raise ValueError(error_message)

        return METRIC_KEY_MAP[normalized_metric]

    def rank_models(self, metric: str = "accuracy") -> List[Dict[str, Any]]:
        """Rank all models in descending order of a chosen metric.

        Args:
            metric: The metric to rank by. One of ``"accuracy"``,
                ``"precision"``, ``"recall"``, ``"f1"``, or ``"roc_auc"``.
                Defaults to ``"accuracy"``.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each with keys
            ``"rank"``, ``"model_name"``, and ``"score"``, sorted from
            best to worst. Models with a missing or ``None`` score for
            the chosen metric are placed at the end.

        Raises:
            ValueError: If ``metric`` is not one of the supported metric
                names.
        """
        metric_key = self._resolve_metric_key(metric)

        scored_models = []
        for model_name, report in self.evaluation_results.items():
            score = report.get(metric_key)
            scored_models.append((model_name, score))

        # Models with a valid score are ranked first (descending), followed
        # by models with a missing score (None), preserving insertion order.
        scored_models.sort(key=lambda item: (item[1] is None, -(item[1] if item[1] is not None else 0)))

        ranking = [
            {"rank": index + 1, "model_name": model_name, "score": score}
            for index, (model_name, score) in enumerate(scored_models)
        ]

        logger.info("Models ranked by '%s': %s", metric, ranking)
        return ranking

    def select_best_model(self, metric: str = "accuracy") -> Dict[str, Any]:
        """Select the best-performing model according to a chosen metric.

        Args:
            metric: The metric used for selection. One of ``"accuracy"``,
                ``"precision"``, ``"recall"``, ``"f1"``, or ``"roc_auc"``.
                Defaults to ``"accuracy"``.

        Returns:
            Dict[str, Any]: A dictionary with keys ``"model_name"``,
            ``"metric"``, and ``"score"`` describing the best model.

        Raises:
            ValueError: If ``metric`` is not supported, or if no model
                has a valid (non-``None``) score for the chosen metric.
        """
        ranking = self.rank_models(metric)

        if not ranking or ranking[0]["score"] is None:
            error_message = f"No model has a valid score for metric '{metric}'."
            logger.error(error_message)
            raise ValueError(error_message)

        best_model = {
            "model_name": ranking[0]["model_name"],
            "metric": metric,
            "score": ranking[0]["score"],
        }
        logger.info("Best model selected using metric '%s': %s", metric, best_model)
        return best_model

    def generate_comparison_report(self, metric: str = "accuracy") -> Dict[str, Any]:
        """Generate a complete model comparison report.

        Args:
            metric: The metric used for ranking and best-model selection.
                One of ``"accuracy"``, ``"precision"``, ``"recall"``,
                ``"f1"``, or ``"roc_auc"``. Defaults to ``"accuracy"``.

        Returns:
            Dict[str, Any]: A dictionary with keys
            ``"comparison_table"`` (as a DataFrame), ``"ranking"``, and
            ``"best_model"``.

        Raises:
            ValueError: If ``metric`` is not supported or no model has a
                valid score for it.
            Exception: Re-raises any other exception encountered while
                generating the report, after logging it.
        """
        try:
            report = {
                "comparison_table": self.build_comparison_table(),
                "ranking": self.rank_models(metric),
                "best_model": self.select_best_model(metric),
            }
            logger.info("Model comparison report generated using metric '%s'.", metric)
            return report
        except ValueError:
            raise
        except Exception as error:
            logger.error("Failed to generate model comparison report: %s", error)
            raise