"""End-to-end preprocessing pipeline for the Risk Assessment module.

This module provides a reusable :class:`PreprocessingPipeline` class that
orchestrates dataset loading (via :class:`DataLoader`), dataset
validation (via :class:`DatasetValidator`), and preprocessing (via
:class:`DataPreprocessor`), then returns the processed train/test splits
along with a summary of everything that occurred. It contains no model
training, evaluation, or plotting logic, and no disease-specific
behavior: the raw dataset path, target column, and column configuration
are all supplied by the caller.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from app.risk_assessment.preprocessing.data_preprocessor import DataPreprocessor
from app.risk_assessment.preprocessing.dataset_validator import DatasetValidator
from app.risk_assessment.utils.data_loader import DataLoader
from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)

DEFAULT_PIPELINE_DIR = Path("risk_assessment/saved_models")
DEFAULT_PROCESSED_DIR = Path("risk_assessment/datasets/processed")


class PreprocessingPipeline:
    """Orchestrate loading, validation, and preprocessing of a raw dataset.

    This class ties together :class:`DataLoader`,
    :class:`DatasetValidator`, and :class:`DataPreprocessor` into a
    single reusable workflow. It contains no disease-specific logic: the
    disease name, dataset path, target column, and column configuration
    (which columns are categorical, which are numerical, and which are
    left unchanged) are all supplied by the caller, so the same class
    works for diabetes, heart disease, stroke, hypertension, or any other
    tabular binary-classification dataset.

    Attributes:
        disease_name: Name of the disease this dataset belongs to, used
            only for output file organization.
        dataset_path: Path to the raw dataset CSV file.
        target_column: Name of the target column in the dataset.
        categorical_columns: Names of columns to one-hot encode.
        numerical_columns: Names of columns to standardize.
        test_size: Proportion of the dataset reserved for testing.
        random_state: Random seed used for the train/test split.
        preprocessor: The :class:`DataPreprocessor` instance used to
            clean, encode, scale, and split the dataset.
    """

    def __init__(
        self,
        disease_name: str,
        dataset_path: Union[str, Path],
        target_column: str,
        categorical_columns: Optional[List[str]] = None,
        numerical_columns: Optional[List[str]] = None,
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> None:
        """Initialize the PreprocessingPipeline.

        Args:
            disease_name: Name of the disease this dataset belongs to
                (e.g., ``"diabetes"``). Used only for output file
                organization; no disease-specific behavior is triggered
                by it.
            dataset_path: Path to the raw dataset CSV file.
            target_column: Name of the target column in the dataset.
            categorical_columns: Names of columns to impute and one-hot
                encode. Defaults to an empty list if not provided.
            numerical_columns: Names of columns to impute and
                standardize. Defaults to an empty list if not provided.
            test_size: Proportion of the dataset reserved for testing.
                Defaults to ``0.2``.
            random_state: Random seed used for the train/test split.
                Defaults to ``42``.
        """
        self.disease_name: str = disease_name
        self.dataset_path: Path = Path(dataset_path)
        self.target_column: str = target_column
        self.categorical_columns: List[str] = categorical_columns or []
        self.numerical_columns: List[str] = numerical_columns or []
        self.test_size: float = test_size
        self.random_state: int = random_state

        self.preprocessor: DataPreprocessor = DataPreprocessor(
            target_column=target_column,
            categorical_columns=self.categorical_columns,
            numerical_columns=self.numerical_columns,
            test_size=test_size,
            random_state=random_state,
        )

    def run(
        self,
        pipeline_output_dir: Optional[Union[str, Path]] = None,
        processed_output_dir: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Any]:
        """Run the full load -> validate -> preprocess -> save workflow.

        Args:
            pipeline_output_dir: Directory in which to save the fitted
                preprocessing pipeline (ColumnTransformer). Defaults to
                ``risk_assessment/saved_models/{disease_name}``.
            processed_output_dir: Directory in which to save the
                processed train/test CSV files. Defaults to
                ``risk_assessment/datasets/processed/{disease_name}``.

        Returns:
            Dict[str, Any]: A dictionary containing:
                ``"disease_name"``, ``"source_file"``,
                ``"validation_report"``, ``"raw_shape"``,
                ``"X_train"``, ``"X_test"``, ``"y_train"``, ``"y_test"``,
                ``"pipeline_path"``, ``"processed_paths"``.

        Raises:
            Exception: Re-raises any exception encountered during
                loading, validation, or preprocessing, after logging it.
        """
        try:
            logger.info(
                "Starting preprocessing pipeline for disease='%s', dataset='%s'.",
                self.disease_name,
                self.dataset_path,
            )

            # Step 1: Load the raw dataset.
            loader = DataLoader(self.dataset_path)
            raw_dataframe = loader.load_csv()

            # Step 2: Validate the raw dataset.
            validator = DatasetValidator(raw_dataframe, target_column=self.target_column)
            validation_report = validator.generate_validation_report()

            # Step 3: Preprocess the dataset (separate, split, encode/scale, save).
            pipeline_dir = (
                Path(pipeline_output_dir)
                if pipeline_output_dir is not None
                else DEFAULT_PIPELINE_DIR / self.disease_name
            )
            processed_dir = (
                Path(processed_output_dir)
                if processed_output_dir is not None
                else DEFAULT_PROCESSED_DIR / self.disease_name
            )

            x_train, x_test, y_train, y_test = self.preprocessor.run(
                raw_dataframe,
                pipeline_output_dir=pipeline_dir,
                processed_output_dir=processed_dir,
                pipeline_file_name=f"{self.disease_name}_preprocessing_pipeline.pkl",
            )

            summary: Dict[str, Any] = {
                "disease_name": self.disease_name,
                "source_file": str(self.dataset_path),
                "validation_report": validation_report,
                "raw_shape": raw_dataframe.shape,
                "X_train": x_train,
                "X_test": x_test,
                "y_train": y_train,
                "y_test": y_test,
                "pipeline_path": str(pipeline_dir / f"{self.disease_name}_preprocessing_pipeline.pkl"),
                "processed_dir": str(processed_dir),
            }

            logger.info(
                "Preprocessing pipeline completed successfully for disease='%s': "
                "X_train=%s, X_test=%s.",
                self.disease_name,
                x_train.shape,
                x_test.shape,
            )
            return summary
        except Exception as error:
            logger.error("Preprocessing pipeline failed: %s", error)
            raise