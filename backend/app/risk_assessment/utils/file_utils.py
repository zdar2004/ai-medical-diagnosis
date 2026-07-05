"""File system utility functions for the Risk Assessment module.

This module provides small, reusable helper functions for working with
directories, files, and pandas DataFrames using ``pathlib``. It contains no
machine learning, preprocessing, or model-related logic.
"""

from pathlib import Path
from typing import Union

import pandas as pd

from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)


def create_directory(directory_path: Union[str, Path]) -> Path:
    """Create a directory, including any missing parent directories.

    If the directory already exists, no error is raised.

    Args:
        directory_path: Path of the directory to create.

    Returns:
        Path: The resolved path of the created (or already existing)
        directory.

    Raises:
        OSError: If the directory cannot be created due to filesystem
            permission issues or an invalid path.
    """
    path = Path(directory_path)

    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.info("Directory ensured: %s", path.resolve())
        return path
    except OSError as error:
        logger.error("Failed to create directory '%s': %s", path, error)
        raise


def file_exists(file_path: Union[str, Path]) -> bool:
    """Check whether a file exists at the given path.

    Args:
        file_path: Path of the file to check.

    Returns:
        bool: ``True`` if the file exists and is a regular file,
        ``False`` otherwise.
    """
    path = Path(file_path)
    exists = path.is_file()

    if exists:
        logger.info("File found: %s", path.resolve())
    else:
        logger.warning("File not found: %s", path.resolve())

    return exists


def save_dataframe(
    dataframe: pd.DataFrame,
    file_path: Union[str, Path],
    index: bool = False,
) -> Path:
    """Save a pandas DataFrame to a CSV file.

    Any missing parent directories in ``file_path`` are created
    automatically.

    Args:
        dataframe: The DataFrame to save.
        file_path: Destination path for the CSV file.
        index: Whether to write the DataFrame index as a column in the
            CSV file. Defaults to ``False``.

    Returns:
        Path: The resolved path where the DataFrame was saved.

    Raises:
        TypeError: If ``dataframe`` is not a pandas DataFrame.
        OSError: If the file cannot be written due to filesystem
            permission issues or an invalid path.
    """
    if not isinstance(dataframe, pd.DataFrame):
        error_message = f"Expected a pandas DataFrame, got {type(dataframe).__name__}"
        logger.error(error_message)
        raise TypeError(error_message)

    path = Path(file_path)

    try:
        create_directory(path.parent)
        dataframe.to_csv(path, index=index)
        logger.info("DataFrame saved to: %s (shape=%s)", path.resolve(), dataframe.shape)
        return path
    except OSError as error:
        logger.error("Failed to save DataFrame to '%s': %s", path, error)
        raise


def load_dataframe(file_path: Union[str, Path]) -> pd.DataFrame:
    """Load a pandas DataFrame from a CSV file.

    Args:
        file_path: Path of the CSV file to load.

    Returns:
        pd.DataFrame: The loaded DataFrame.

    Raises:
        FileNotFoundError: If no file exists at ``file_path``.
        pd.errors.EmptyDataError: If the file exists but contains no data.
        OSError: If the file cannot be read due to filesystem permission
            issues.
    """
    path = Path(file_path)

    if not file_exists(path):
        error_message = f"Cannot load DataFrame, file does not exist: {path}"
        logger.error(error_message)
        raise FileNotFoundError(error_message)

    try:
        dataframe = pd.read_csv(path)
        logger.info("DataFrame loaded from: %s (shape=%s)", path.resolve(), dataframe.shape)
        return dataframe
    except pd.errors.EmptyDataError as error:
        logger.error("File '%s' is empty: %s", path, error)
        raise
    except OSError as error:
        logger.error("Failed to load DataFrame from '%s': %s", path, error)
        raise