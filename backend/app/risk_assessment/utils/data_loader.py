"""Dataset loading utilities for the Risk Assessment module.

This module provides a reusable :class:`DataLoader` class responsible
solely for loading raw CSV datasets into pandas DataFrames. It performs no
preprocessing, feature engineering, or transformation of any kind.
"""

from pathlib import Path
from typing import Union

import pandas as pd

from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)


class DataLoader:
    """Load CSV datasets into pandas DataFrames.

    This class is intentionally limited to dataset loading concerns:
    validating that a file exists, reading it into memory, and reporting
    basic information about the resulting DataFrame (shape and column
    names). It performs no cleaning, encoding, scaling, or other
    preprocessing.

    Attributes:
        file_path: Path to the CSV dataset that this loader targets.
    """

    def __init__(self, file_path: Union[str, Path]) -> None:
        """Initialize the DataLoader with a target CSV file path.

        Args:
            file_path: Path to the CSV dataset to be loaded.
        """
        self.file_path: Path = Path(file_path)

    def validate_file_exists(self) -> bool:
        """Check whether the target CSV file exists on disk.

        Returns:
            bool: ``True`` if the file exists and is a regular file,
            ``False`` otherwise.
        """
        exists = self.file_path.is_file()

        if exists:
            logger.info("Dataset file located: %s", self.file_path.resolve())
        else:
            logger.warning("Dataset file not found: %s", self.file_path.resolve())

        return exists

    def load_csv(self) -> pd.DataFrame:
        """Load the target CSV file into a pandas DataFrame.

        Validates that the file exists before attempting to read it, and
        logs the resulting dataset's shape and column names on success.

        Returns:
            pd.DataFrame: The loaded dataset.

        Raises:
            FileNotFoundError: If the target CSV file does not exist.
            pd.errors.EmptyDataError: If the CSV file exists but contains
                no data.
            pd.errors.ParserError: If the CSV file cannot be parsed.
            OSError: If the file cannot be read due to filesystem
                permission issues.
        """
        if not self.validate_file_exists():
            error_message = f"CSV file does not exist: {self.file_path}"
            logger.error(error_message)
            raise FileNotFoundError(error_message)

        try:
            dataframe = pd.read_csv(self.file_path)
            logger.info("Dataset loaded successfully: %s", self.file_path.resolve())
            self._log_dataset_info(dataframe)
            return dataframe
        except pd.errors.EmptyDataError as error:
            logger.error("Dataset file is empty: %s (%s)", self.file_path, error)
            raise
        except pd.errors.ParserError as error:
            logger.error("Failed to parse dataset file: %s (%s)", self.file_path, error)
            raise
        except OSError as error:
            logger.error("Failed to read dataset file: %s (%s)", self.file_path, error)
            raise

    def show_shape(self, dataframe: pd.DataFrame) -> tuple:
        """Log and return the shape of a DataFrame.

        Args:
            dataframe: The DataFrame whose shape should be reported.

        Returns:
            tuple: The ``(rows, columns)`` shape of the DataFrame.
        """
        shape = dataframe.shape
        logger.info("Dataset shape: %s", shape)
        return shape

    def show_columns(self, dataframe: pd.DataFrame) -> list:
        """Log and return the column names of a DataFrame.

        Args:
            dataframe: The DataFrame whose columns should be reported.

        Returns:
            list: The list of column names in the DataFrame.
        """
        columns = list(dataframe.columns)
        logger.info("Dataset columns: %s", columns)
        return columns

    def _log_dataset_info(self, dataframe: pd.DataFrame) -> None:
        """Log basic information (shape and columns) about a DataFrame.

        Args:
            dataframe: The DataFrame to describe in the logs.
        """
        self.show_shape(dataframe)
        self.show_columns(dataframe)