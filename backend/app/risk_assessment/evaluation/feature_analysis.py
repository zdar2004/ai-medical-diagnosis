"""Feature analysis utilities for the Risk Assessment module.

This module provides a reusable :class:`FeatureAnalysis` class that
identifies feature types (numerical, categorical, binary), computes
correlation matrices and target correlations, and flags highly
correlated feature pairs. It also exposes a non-ML feature importance
placeholder. This module performs no plotting, preprocessing, or model
training.
"""

from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)

DEFAULT_CORRELATION_THRESHOLD = 0.8


class FeatureAnalysis:
    """Analyze feature types and relationships within a tabular dataset.

    This class is disease-agnostic and works with any pandas DataFrame.
    It identifies numerical, categorical, and binary features, computes
    correlation matrices, reports target correlations, and flags highly
    correlated feature pairs. It does not preprocess data, generate
    plots, or train models.

    Attributes:
        dataframe: The pandas DataFrame being analyzed.
        target_column: Optional name of the target column, used for
            target-correlation reporting.
    """

    def __init__(
        self, dataframe: pd.DataFrame, target_column: Optional[str] = None
    ) -> None:
        """Initialize the FeatureAnalysis.

        Args:
            dataframe: The pandas DataFrame to analyze.
            target_column: Optional name of the target column, used when
                computing target correlations. If ``None``, target
                correlation reporting will be skipped.

        Raises:
            TypeError: If ``dataframe`` is not a pandas DataFrame.
        """
        if not isinstance(dataframe, pd.DataFrame):
            error_message = (
                f"Expected a pandas DataFrame, got {type(dataframe).__name__}"
            )
            logger.error(error_message)
            raise TypeError(error_message)

        self.dataframe: pd.DataFrame = dataframe
        self.target_column: Optional[str] = target_column

    def identify_numerical_features(self) -> List[str]:
        """Identify columns with numerical datatypes.

        Returns:
            List[str]: Names of columns with numerical dtypes.
        """
        numerical_features = list(self.dataframe.select_dtypes(include="number").columns)
        logger.info("Identified numerical features: %s", numerical_features)
        return numerical_features

    def identify_categorical_features(self) -> List[str]:
        """Identify columns with non-numerical (categorical) datatypes.

        Returns:
            List[str]: Names of columns with object or category dtypes.
        """
        categorical_features = list(self.dataframe.select_dtypes(exclude="number").columns)
        logger.info("Identified categorical features: %s", categorical_features)
        return categorical_features

    def identify_binary_features(self) -> List[str]:
        """Identify columns that contain exactly two unique values.

        A column is considered binary if it has exactly two distinct
        non-null values, regardless of its underlying datatype.

        Returns:
            List[str]: Names of columns with exactly two unique values.
        """
        binary_features = [
            column
            for column in self.dataframe.columns
            if self.dataframe[column].nunique(dropna=True) == 2
        ]
        logger.info("Identified binary features: %s", binary_features)
        return binary_features

    def compute_correlation_matrix(self, method: str = "pearson") -> pd.DataFrame:
        """Compute the correlation matrix for numerical columns.

        Args:
            method: Correlation method to use. One of ``"pearson"``,
                ``"kendall"``, or ``"spearman"``. Defaults to
                ``"pearson"``.

        Returns:
            pd.DataFrame: The correlation matrix as a DataFrame. Returns
            an empty DataFrame if there are fewer than two numerical
            columns.

        Raises:
            ValueError: If ``method`` is not a supported correlation
                method.
        """
        supported_methods = {"pearson", "kendall", "spearman"}
        if method not in supported_methods:
            error_message = f"Unsupported correlation method '{method}'. Expected one of {supported_methods}."
            logger.error(error_message)
            raise ValueError(error_message)

        numeric_dataframe = self.dataframe.select_dtypes(include="number")

        if numeric_dataframe.shape[1] < 2:
            logger.warning("Fewer than two numerical columns available; returning empty correlation matrix.")
            return pd.DataFrame()

        correlation_matrix = numeric_dataframe.corr(method=method)
        logger.info("Correlation matrix computed using method='%s'.", method)
        return correlation_matrix

    def compute_target_correlation(self, method: str = "pearson") -> Dict[str, float]:
        """Compute correlation of each numerical feature with the target column.

        Args:
            method: Correlation method to use. One of ``"pearson"``,
                ``"kendall"``, or ``"spearman"``. Defaults to
                ``"pearson"``.

        Returns:
            Dict[str, float]: A mapping of feature name to its
            correlation coefficient with the target column, sorted by
            absolute correlation in descending order. Returns an empty
            dictionary if no target column is set, the target column is
            missing, or the target column is not numeric.
        """
        if self.target_column is None or self.target_column not in self.dataframe.columns:
            logger.warning(
                "Target column '%s' unavailable; skipping target correlation.",
                self.target_column,
            )
            return {}

        numeric_dataframe = self.dataframe.select_dtypes(include="number")

        if self.target_column not in numeric_dataframe.columns:
            logger.warning(
                "Target column '%s' is not numeric; skipping target correlation.",
                self.target_column,
            )
            return {}

        correlations = numeric_dataframe.corr(method=method)[self.target_column].drop(
            labels=[self.target_column], errors="ignore"
        )
        sorted_correlations = correlations.reindex(
            correlations.abs().sort_values(ascending=False).index
        )

        result = sorted_correlations.to_dict()
        logger.info("Target correlation computed for '%s': %s", self.target_column, result)
        return result

    def find_highly_correlated_pairs(
        self, threshold: float = DEFAULT_CORRELATION_THRESHOLD, method: str = "pearson"
    ) -> List[Tuple[str, str, float]]:
        """Identify pairs of numerical features with high mutual correlation.

        Args:
            threshold: Absolute correlation value above which a feature
                pair is considered highly correlated. Defaults to ``0.8``.
            method: Correlation method to use. One of ``"pearson"``,
                ``"kendall"``, or ``"spearman"``. Defaults to
                ``"pearson"``.

        Returns:
            List[Tuple[str, str, float]]: A list of
            ``(feature_a, feature_b, correlation)`` tuples for pairs whose
            absolute correlation exceeds ``threshold``, sorted by
            absolute correlation in descending order.

        Raises:
            ValueError: If ``threshold`` is not between 0 and 1.
        """
        if not 0.0 <= threshold <= 1.0:
            error_message = f"threshold must be between 0 and 1, got {threshold}."
            logger.error(error_message)
            raise ValueError(error_message)

        correlation_matrix = self.compute_correlation_matrix(method=method)

        if correlation_matrix.empty:
            logger.warning("No correlation matrix available; returning empty pair list.")
            return []

        highly_correlated_pairs: List[Tuple[str, str, float]] = []
        columns = correlation_matrix.columns

        for i, column_a in enumerate(columns):
            for column_b in columns[i + 1:]:
                correlation_value = correlation_matrix.loc[column_a, column_b]
                if abs(correlation_value) >= threshold:
                    highly_correlated_pairs.append((column_a, column_b, round(float(correlation_value), 4)))

        highly_correlated_pairs.sort(key=lambda pair: abs(pair[2]), reverse=True)

        logger.info(
            "Found %d highly correlated feature pair(s) at threshold=%.2f: %s",
            len(highly_correlated_pairs),
            threshold,
            highly_correlated_pairs,
        )
        return highly_correlated_pairs

    def get_feature_importance_placeholder(self) -> Dict[str, Any]:
        """Return a non-ML placeholder for feature importance.

        This method does not train any model or compute true feature
        importance scores. It exists as an architectural placeholder so
        that downstream modules (e.g., training/evaluation) have a
        consistent interface to call once real feature-importance logic
        is implemented elsewhere.

        Returns:
            Dict[str, Any]: A dictionary indicating that feature
            importance has not been computed, along with the list of
            candidate feature columns (all columns excluding the target).
        """
        feature_columns = [
            column for column in self.dataframe.columns if column != self.target_column
        ]

        placeholder = {
            "status": "not_computed",
            "message": "Feature importance requires a trained model and is not computed here.",
            "candidate_features": feature_columns,
        }
        logger.info("Feature importance placeholder generated for %d feature(s).", len(feature_columns))
        return placeholder

    def generate_feature_analysis_report(
        self, correlation_threshold: float = DEFAULT_CORRELATION_THRESHOLD
    ) -> Dict[str, Any]:
        """Generate a complete feature analysis report.

        Combines feature-type identification, correlation analysis, and
        the feature importance placeholder into a single dictionary.

        Args:
            correlation_threshold: Threshold used when identifying highly
                correlated feature pairs. Defaults to ``0.8``.

        Returns:
            Dict[str, Any]: A dictionary with keys
            ``"numerical_features"``, ``"categorical_features"``,
            ``"binary_features"``, ``"correlation_matrix"`` (as a
            DataFrame), ``"target_correlation"``,
            ``"highly_correlated_pairs"``, ``"feature_importance"``.

        Raises:
            Exception: Re-raises any exception encountered while
                generating the report, after logging it.
        """
        try:
            report: Dict[str, Any] = {
                "numerical_features": self.identify_numerical_features(),
                "categorical_features": self.identify_categorical_features(),
                "binary_features": self.identify_binary_features(),
                "correlation_matrix": self.compute_correlation_matrix(),
                "target_correlation": self.compute_target_correlation(),
                "highly_correlated_pairs": self.find_highly_correlated_pairs(
                    threshold=correlation_threshold
                ),
                "feature_importance": self.get_feature_importance_placeholder(),
            }
            logger.info("Feature analysis report generated successfully.")
            return report
        except Exception as error:
            logger.error("Failed to generate feature analysis report: %s", error)
            raise