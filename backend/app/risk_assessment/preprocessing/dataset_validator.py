"""Dataset validation utilities for the Risk Assessment module.

This module provides a reusable :class:`DatasetValidator` class that
inspects a pandas DataFrame and reports data-quality information such as
missing values, duplicate rows, shape, column names, target column
presence, and datatype summaries. It performs no plotting, preprocessing,
feature engineering, or model-related logic.
"""

from typing import Any, Dict, Optional

import pandas as pd

from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)


class DatasetValidator:
    """Validate a dataset and generate a structured validation report.

    This class inspects a pandas DataFrame for common data-quality
    concerns (missing values, duplicate rows, shape, column names,
    target column presence, and datatypes) and compiles the findings into
    a single validation report dictionary. It does not modify the
    DataFrame in any way.

    Attributes:
        dataframe: The pandas DataFrame under validation.
        target_column: Optional name of the expected target column.
    """

    def __init__(
        self, dataframe: pd.DataFrame, target_column: Optional[str] = None
    ) -> None:
        """Initialize the DatasetValidator.

        Args:
            dataframe: The pandas DataFrame to validate.
            target_column: Name of the expected target column, if known.
                If ``None``, target column checks will be skipped.

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

    def check_missing_values(self) -> Dict[str, int]:
        """Count missing values per column.

        Returns:
            Dict[str, int]: A mapping of column name to the number of
            missing (NaN) values in that column.
        """
        missing_counts = self.dataframe.isnull().sum().to_dict()
        logger.info("Missing value check complete: %s", missing_counts)
        return missing_counts

    def check_duplicate_rows(self) -> int:
        """Count the number of fully duplicated rows in the dataset.

        Returns:
            int: The number of duplicate rows found.
        """
        duplicate_count = int(self.dataframe.duplicated().sum())
        logger.info("Duplicate row check complete: %d duplicate(s) found.", duplicate_count)
        return duplicate_count

    def check_shape(self) -> tuple:
        """Report the shape of the dataset.

        Returns:
            tuple: The ``(rows, columns)`` shape of the DataFrame.
        """
        shape = self.dataframe.shape
        logger.info("Dataset shape: %s", shape)
        return shape

    def check_columns(self) -> list:
        """Report the column names of the dataset.

        Returns:
            list: The list of column names in the DataFrame.
        """
        columns = list(self.dataframe.columns)
        logger.info("Dataset columns: %s", columns)
        return columns

    def check_target_column_exists(self) -> bool:
        """Check whether the expected target column exists in the dataset.

        Returns:
            bool: ``True`` if a target column was specified and is present
            in the DataFrame, ``False`` otherwise (including when no
            target column was specified).
        """
        if self.target_column is None:
            logger.warning("No target column specified; skipping target check.")
            return False

        exists = self.target_column in self.dataframe.columns

        if exists:
            logger.info("Target column '%s' found in dataset.", self.target_column)
        else:
            logger.warning(
                "Target column '%s' not found in dataset columns: %s",
                self.target_column,
                list(self.dataframe.columns),
            )

        return exists

    def check_dtypes(self) -> Dict[str, str]:
        """Summarize the datatype of each column.

        Returns:
            Dict[str, str]: A mapping of column name to its datatype, as a
            string (e.g., ``"int64"``, ``"float64"``, ``"object"``).
        """
        dtype_summary = {
            column: str(dtype) for column, dtype in self.dataframe.dtypes.items()
        }
        logger.info("Datatype summary: %s", dtype_summary)
        return dtype_summary

    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate a complete validation report for the dataset.

        Combines the results of all individual checks (missing values,
        duplicate rows, shape, columns, target column presence, and
        datatypes) into a single dictionary.

        Returns:
            Dict[str, Any]: A dictionary with the following keys:
                ``"shape"``, ``"columns"``, ``"missing_values"``,
                ``"duplicate_rows"``, ``"target_column_exists"``,
                ``"dtypes"``.

        Raises:
            Exception: Re-raises any exception encountered while running
                the individual validation checks, after logging it.
        """
        try:
            report: Dict[str, Any] = {
                "shape": self.check_shape(),
                "columns": self.check_columns(),
                "missing_values": self.check_missing_values(),
                "duplicate_rows": self.check_duplicate_rows(),
                "target_column_exists": self.check_target_column_exists(),
                "dtypes": self.check_dtypes(),
            }
            logger.info("Validation report generated successfully.")
            return report
        except Exception as error:
            logger.error("Failed to generate validation report: %s", error)
            raise