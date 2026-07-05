"""Dataset summary utilities for the Risk Assessment module.

This module provides a reusable :class:`DatasetSummary` class that
computes descriptive statistics about a tabular dataset: shape, column
names, datatypes, missing values, duplicate rows, class distribution, and
numerical/categorical statistics. All results are returned as
dictionaries. This module contains no plotting and no machine learning
logic.
"""

from typing import Any, Dict, Optional

import pandas as pd

from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)


class DatasetSummary:
    """Compute descriptive summary statistics for a tabular dataset.

    This class is disease-agnostic and works with any pandas DataFrame.
    It reports structural information (shape, columns, dtypes), data
    quality information (missing values, duplicates), and descriptive
    statistics (numerical and categorical), all returned as plain
    dictionaries. No plots are generated and no models are trained.

    Attributes:
        dataframe: The pandas DataFrame being summarized.
        target_column: Optional name of the target column, used for
            class distribution reporting.
    """

    def __init__(
        self, dataframe: pd.DataFrame, target_column: Optional[str] = None
    ) -> None:
        """Initialize the DatasetSummary.

        Args:
            dataframe: The pandas DataFrame to summarize.
            target_column: Optional name of the target column, used when
                computing class distribution. If ``None``, class
                distribution reporting will be skipped.

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

    def get_shape(self) -> Dict[str, int]:
        """Report the number of rows and columns in the dataset.

        Returns:
            Dict[str, int]: A dictionary with keys ``"rows"`` and
            ``"columns"``.
        """
        summary = {
            "rows": self.dataframe.shape[0],
            "columns": self.dataframe.shape[1],
        }
        logger.info("Dataset shape summary: %s", summary)
        return summary

    def get_column_names(self) -> Dict[str, list]:
        """Report the column names of the dataset.

        Returns:
            Dict[str, list]: A dictionary with key ``"column_names"``
            mapping to the list of column names.
        """
        summary = {"column_names": list(self.dataframe.columns)}
        logger.info("Column names retrieved: %s", summary["column_names"])
        return summary

    def get_dtypes(self) -> Dict[str, str]:
        """Report the datatype of each column.

        Returns:
            Dict[str, str]: A mapping of column name to its datatype, as
            a string.
        """
        dtypes = {column: str(dtype) for column, dtype in self.dataframe.dtypes.items()}
        logger.info("Datatype summary: %s", dtypes)
        return dtypes

    def get_missing_values_summary(self) -> Dict[str, Any]:
        """Summarize missing values per column, as counts and percentages.

        Returns:
            Dict[str, Any]: A dictionary with keys ``"missing_counts"``
            (column -> count) and ``"missing_percentages"``
            (column -> percentage of total rows).
        """
        total_rows = len(self.dataframe)
        missing_counts = self.dataframe.isnull().sum().to_dict()

        missing_percentages = {
            column: round((count / total_rows) * 100, 2) if total_rows > 0 else 0.0
            for column, count in missing_counts.items()
        }

        summary = {
            "missing_counts": missing_counts,
            "missing_percentages": missing_percentages,
        }
        logger.info("Missing values summary computed: %s", summary)
        return summary

    def get_duplicate_count(self) -> Dict[str, int]:
        """Report the number of fully duplicated rows in the dataset.

        Returns:
            Dict[str, int]: A dictionary with key ``"duplicate_rows"``.
        """
        duplicate_count = int(self.dataframe.duplicated().sum())
        summary = {"duplicate_rows": duplicate_count}
        logger.info("Duplicate row count: %s", summary)
        return summary

    def get_class_distribution(self) -> Dict[str, Any]:
        """Report the class distribution of the target column.

        Returns:
            Dict[str, Any]: A dictionary with keys ``"counts"``
            (class label -> count) and ``"percentages"``
            (class label -> percentage of total rows). Returns an empty
            dictionary if no target column was specified or if it is not
            present in the dataset.
        """
        if self.target_column is None or self.target_column not in self.dataframe.columns:
            logger.warning(
                "Target column '%s' unavailable; skipping class distribution.",
                self.target_column,
            )
            return {}

        value_counts = self.dataframe[self.target_column].value_counts()
        percentages = self.dataframe[self.target_column].value_counts(normalize=True) * 100

        summary = {
            "counts": value_counts.to_dict(),
            "percentages": {label: round(value, 2) for label, value in percentages.to_dict().items()},
        }
        logger.info("Class distribution for '%s': %s", self.target_column, summary)
        return summary

    def get_numerical_statistics(self) -> Dict[str, Any]:
        """Compute descriptive statistics for numerical columns.

        Returns:
            Dict[str, Any]: A nested dictionary of the form
            ``{column: {"mean": ..., "std": ..., "min": ..., "25%": ...,
            "50%": ..., "75%": ..., "max": ...}}``. Returns an empty
            dictionary if there are no numerical columns.
        """
        numeric_dataframe = self.dataframe.select_dtypes(include="number")

        if numeric_dataframe.empty:
            logger.warning("No numerical columns found for statistics.")
            return {}

        statistics = numeric_dataframe.describe().to_dict()
        logger.info("Numerical statistics computed for columns: %s", list(statistics.keys()))
        return statistics

    def get_categorical_statistics(self) -> Dict[str, Any]:
        """Compute descriptive statistics for categorical columns.

        Returns:
            Dict[str, Any]: A nested dictionary of the form
            ``{column: {"unique_count": ..., "top": ..., "top_frequency":
            ..., "value_counts": {...}}}``. Returns an empty dictionary if
            there are no categorical columns.
        """
        categorical_dataframe = self.dataframe.select_dtypes(exclude="number")

        if categorical_dataframe.empty:
            logger.warning("No categorical columns found for statistics.")
            return {}

        statistics: Dict[str, Any] = {}
        for column in categorical_dataframe.columns:
            value_counts = categorical_dataframe[column].value_counts()
            statistics[column] = {
                "unique_count": int(categorical_dataframe[column].nunique()),
                "top": value_counts.index[0] if not value_counts.empty else None,
                "top_frequency": int(value_counts.iloc[0]) if not value_counts.empty else 0,
                "value_counts": value_counts.to_dict(),
            }

        logger.info("Categorical statistics computed for columns: %s", list(statistics.keys()))
        return statistics

    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate a complete dataset summary report.

        Combines the results of all individual summary methods into a
        single dictionary.

        Returns:
            Dict[str, Any]: A dictionary with keys ``"shape"``,
            ``"column_names"``, ``"dtypes"``, ``"missing_values"``,
            ``"duplicate_count"``, ``"class_distribution"``,
            ``"numerical_statistics"``, ``"categorical_statistics"``.

        Raises:
            Exception: Re-raises any exception encountered while
                generating the report, after logging it.
        """
        try:
            report: Dict[str, Any] = {
                "shape": self.get_shape(),
                "column_names": self.get_column_names(),
                "dtypes": self.get_dtypes(),
                "missing_values": self.get_missing_values_summary(),
                "duplicate_count": self.get_duplicate_count(),
                "class_distribution": self.get_class_distribution(),
                "numerical_statistics": self.get_numerical_statistics(),
                "categorical_statistics": self.get_categorical_statistics(),
            }
            logger.info("Dataset summary report generated successfully.")
            return report
        except Exception as error:
            logger.error("Failed to generate dataset summary report: %s", error)
            raise