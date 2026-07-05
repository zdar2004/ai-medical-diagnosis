"""Dataset management utilities for the Risk Assessment module.

This module provides a reusable :class:`DatasetManager` class responsible
for locating raw dataset files on disk, listing what is available, and
returning dataset paths. It uses :class:`DataLoader` internally to read
CSV files, but performs no preprocessing, cleaning, or feature
engineering of any kind.
"""

from pathlib import Path
from typing import Dict, List, Union

import pandas as pd

from app.risk_assessment.utils.data_loader import DataLoader
from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)

DEFAULT_RAW_DATA_DIR = Path("risk_assessment/datasets/raw")


class DatasetManager:
    """Locate and manage raw datasets stored under ``datasets/raw``.

    This class is responsible for discovering dataset files within the
    raw data directory structure (organized by disease subfolder),
    validating that the expected directory layout exists, and loading
    individual datasets on demand via :class:`DataLoader`. It performs no
    preprocessing or transformation of the underlying data.

    Attributes:
        raw_data_dir: Root directory containing raw dataset subfolders.
    """

    def __init__(self, raw_data_dir: Union[str, Path] = DEFAULT_RAW_DATA_DIR) -> None:
        """Initialize the DatasetManager with a raw dataset root directory.

        Args:
            raw_data_dir: Root directory containing raw dataset
                subfolders (e.g., ``diabetes``, ``heart_disease``,
                ``stroke``, ``hypertension``). Defaults to
                ``risk_assessment/datasets/raw``.
        """
        self.raw_data_dir: Path = Path(raw_data_dir)

    def validate_directory_structure(self) -> bool:
        """Validate that the raw dataset root directory exists.

        Returns:
            bool: ``True`` if the raw data directory exists and is a
            directory, ``False`` otherwise.
        """
        is_valid = self.raw_data_dir.is_dir()

        if is_valid:
            logger.info("Raw dataset directory found: %s", self.raw_data_dir.resolve())
        else:
            logger.warning(
                "Raw dataset directory not found: %s", self.raw_data_dir.resolve()
            )

        return is_valid

    def list_available_datasets(self) -> Dict[str, List[Path]]:
        """List all CSV dataset files available under the raw data directory.

        Datasets are grouped by their immediate parent subfolder name
        (typically a disease category, e.g. ``diabetes``).

        Returns:
            Dict[str, List[Path]]: A mapping of subfolder name to a list
            of CSV file paths found within it. Returns an empty dictionary
            if the raw data directory does not exist.

        Raises:
            OSError: If the directory contents cannot be read due to
                filesystem permission issues.
        """
        if not self.validate_directory_structure():
            logger.warning("Cannot list datasets, raw data directory is missing.")
            return {}

        available_datasets: Dict[str, List[Path]] = {}

        try:
            for entry in sorted(self.raw_data_dir.iterdir()):
                if entry.is_dir():
                    csv_files = sorted(entry.glob("*.csv"))
                    if csv_files:
                        available_datasets[entry.name] = csv_files
                        logger.info(
                            "Found %d dataset(s) in '%s': %s",
                            len(csv_files),
                            entry.name,
                            [file.name for file in csv_files],
                        )
                    else:
                        logger.warning("No CSV files found in subfolder: %s", entry.name)
                elif entry.suffix == ".csv":
                    # CSV files placed directly under the raw data root.
                    available_datasets.setdefault("_root", []).append(entry)
                    logger.info("Found dataset directly under raw root: %s", entry.name)
        except OSError as error:
            logger.error(
                "Failed to list datasets in '%s': %s", self.raw_data_dir, error
            )
            raise

        return available_datasets

    def get_dataset_path(self, category: str, file_name: str) -> Path:
        """Return the path to a specific dataset file within a category.

        Args:
            category: Name of the dataset subfolder (e.g., ``"diabetes"``).
            file_name: Name of the CSV file, including its extension.

        Returns:
            Path: The resolved path to the requested dataset file.

        Raises:
            FileNotFoundError: If the resulting path does not point to an
                existing file.
        """
        dataset_path = self.raw_data_dir / category / file_name

        if not dataset_path.is_file():
            error_message = f"Dataset file not found: {dataset_path}"
            logger.error(error_message)
            raise FileNotFoundError(error_message)

        logger.info("Resolved dataset path: %s", dataset_path.resolve())
        return dataset_path

    def load_dataset(self, category: str, file_name: str) -> pd.DataFrame:
        """Load a specific dataset into a pandas DataFrame.

        Internally resolves the dataset path and delegates the actual
        file reading to :class:`DataLoader`.

        Args:
            category: Name of the dataset subfolder (e.g., ``"diabetes"``).
            file_name: Name of the CSV file, including its extension.

        Returns:
            pd.DataFrame: The loaded dataset.

        Raises:
            FileNotFoundError: If the dataset file does not exist.
        """
        dataset_path = self.get_dataset_path(category, file_name)
        loader = DataLoader(dataset_path)
        dataframe = loader.load_csv()

        logger.info(
            "Dataset '%s/%s' loaded via DataLoader.", category, file_name
        )
        return dataframe