"""Model training pipeline for the Risk Assessment module.

This module provides a reusable :class:`TrainingPipeline` class that
loads the already-preprocessed, already-split train/test datasets
produced by the preprocessing module (``X_train.csv``, ``X_test.csv``,
``y_train.csv``, ``y_test.csv``), obtains a model from
:class:`ModelFactory`, trains it on the training split, saves the
trained model with ``joblib``, and returns a training summary that
includes the held-out test set for downstream evaluation. The same
pipeline works for any disease and any supported model; it contains no
disease-specific logic, no evaluation, and no preprocessing of its own.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import joblib
import pandas as pd

from app.risk_assessment.training.model_factory import ModelFactory
from app.risk_assessment.utils.data_loader import DataLoader
from app.risk_assessment.utils.file_utils import create_directory
from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)

DEFAULT_X_TRAIN_FILE_NAME = "X_train.csv"
DEFAULT_X_TEST_FILE_NAME = "X_test.csv"
DEFAULT_Y_TRAIN_FILE_NAME = "y_train.csv"
DEFAULT_Y_TEST_FILE_NAME = "y_test.csv"


class TrainingPipeline:
    """Train and persist a machine learning model for a risk assessment dataset.

    This class is fully generic: the disease name, model name, target
    column, processed data directory, and save directory are all
    supplied by the caller. It contains no disease-specific logic and
    works identically for diabetes, heart disease, stroke, hypertension,
    or any other tabular binary-classification dataset. It performs no
    preprocessing or splitting of its own: it consumes the already-split
    ``X_train.csv``, ``X_test.csv``, ``y_train.csv``, and ``y_test.csv``
    files produced by the preprocessing module, and it performs no
    evaluation or plotting.

    Attributes:
        disease_name: Name of the disease this model is being trained
            for (used only for logging and output file naming).
        model_name: Name of the model to obtain from
            :class:`ModelFactory`.
        target_column: Name of the target column (used to read the
            target value out of the single-column ``y_train``/``y_test``
            CSV files).
        processed_data_dir: Directory containing the preprocessed
            ``X_train.csv``, ``X_test.csv``, ``y_train.csv``, and
            ``y_test.csv`` files.
        save_directory: Directory in which the trained model will be
            saved.
        model_params: Optional hyperparameters passed to
            :class:`ModelFactory`.
    """

    def __init__(
        self,
        disease_name: str,
        model_name: str,
        target_column: str,
        processed_data_dir: Union[str, Path],
        save_directory: Union[str, Path],
        model_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the TrainingPipeline.

        Args:
            disease_name: Name of the disease being modeled (e.g.,
                ``"diabetes"``). Used only for logging and output file
                naming; no disease-specific behavior is triggered by it.
            model_name: Name of the model to train. Must be one of the
                names supported by :class:`ModelFactory`.
            target_column: Name of the target column, used to extract
                the target values from the ``y_train``/``y_test`` CSV
                files.
            processed_data_dir: Directory containing the preprocessed
                ``X_train.csv``, ``X_test.csv``, ``y_train.csv``, and
                ``y_test.csv`` files, as produced by the preprocessing
                module.
            save_directory: Directory in which to save the trained model.
            model_params: Optional dictionary of hyperparameters to pass
                to :class:`ModelFactory` when instantiating the model.
        """
        self.disease_name: str = disease_name
        self.model_name: str = model_name
        self.target_column: str = target_column
        self.processed_data_dir: Path = Path(processed_data_dir)
        self.save_directory: Path = Path(save_directory)
        self.model_params: Optional[Dict[str, Any]] = model_params

    def _load_features(self, file_name: str) -> pd.DataFrame:
        """Load a preprocessed feature matrix CSV file.

        Args:
            file_name: Name of the feature CSV file (e.g.,
                ``"X_train.csv"``) within ``processed_data_dir``.

        Returns:
            pd.DataFrame: The loaded feature matrix.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        file_path = self.processed_data_dir / file_name
        loader = DataLoader(file_path)
        dataframe = loader.load_csv()

        logger.info(
            "Loaded features for disease='%s' from '%s' (shape=%s).",
            self.disease_name,
            file_path,
            dataframe.shape,
        )
        return dataframe

    def _load_target(self, file_name: str) -> pd.Series:
        """Load a preprocessed target vector CSV file.

        Args:
            file_name: Name of the target CSV file (e.g.,
                ``"y_train.csv"``) within ``processed_data_dir``.

        Returns:
            pd.Series: The loaded target values.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        file_path = self.processed_data_dir / file_name
        loader = DataLoader(file_path)
        dataframe = loader.load_csv()

        target_series = (
            dataframe[self.target_column]
            if self.target_column in dataframe.columns
            else dataframe.iloc[:, 0]
        )

        logger.info(
            "Loaded target for disease='%s' from '%s' (shape=%s).",
            self.disease_name,
            file_path,
            target_series.shape,
        )
        return target_series

    def load_datasets(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """Load the preprocessed train/test feature and target sets.

        Reads ``X_train.csv``, ``X_test.csv``, ``y_train.csv``, and
        ``y_test.csv`` from ``processed_data_dir``.

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
            ``(X_train, X_test, y_train, y_test)``.

        Raises:
            FileNotFoundError: If any of the expected files do not
                exist.
        """
        x_train = self._load_features(DEFAULT_X_TRAIN_FILE_NAME)
        x_test = self._load_features(DEFAULT_X_TEST_FILE_NAME)
        y_train = self._load_target(DEFAULT_Y_TRAIN_FILE_NAME)
        y_test = self._load_target(DEFAULT_Y_TEST_FILE_NAME)

        logger.info(
            "Loaded preprocessed datasets for disease='%s': train=%s, test=%s.",
            self.disease_name,
            x_train.shape,
            x_test.shape,
        )
        return x_train, x_test, y_train, y_test

    def get_model(self) -> Any:
        """Obtain an untrained model instance from :class:`ModelFactory`.

        Returns:
            Any: An untrained model instance corresponding to
            ``self.model_name``.

        Raises:
            ValueError: If ``self.model_name`` is not supported.
            ImportError: If ``self.model_name`` is ``"xgboost"`` and the
                ``xgboost`` package is not installed.
        """
        model = ModelFactory.get_model(self.model_name, model_params=self.model_params)
        logger.info(
            "Obtained model '%s' for disease='%s'.", self.model_name, self.disease_name
        )
        return model

    def save_model(self, model: Any) -> Path:
        """Persist a trained model to disk using joblib.

        The model is saved under ``save_directory`` using a filename of
        the form ``{disease_name}_{model_name}.pkl``.

        Args:
            model: The trained model instance to save.

        Returns:
            Path: The resolved path where the model was saved.

        Raises:
            OSError: If the model file cannot be written due to
                filesystem permission issues.
        """
        try:
            create_directory(self.save_directory)
            file_name = f"{self.disease_name}_{self.model_name}.pkl"
            file_path = self.save_directory / file_name

            joblib.dump(model, file_path)
            logger.info("Trained model saved to: %s", file_path.resolve())
            return file_path
        except OSError as error:
            logger.error("Failed to save trained model to '%s': %s", self.save_directory, error)
            raise

    def run(self, save_model: bool = True) -> Dict[str, Any]:
        """Run the full training workflow: load, train, and optionally save.

        Args:
            save_model: Whether to persist the trained model to disk via
                :meth:`save_model`. Defaults to ``True``.

        Returns:
            Dict[str, Any]: A training result dictionary containing:
                ``"disease_name"``, ``"model_name"``, ``"target_column"``,
                ``"train_shape"``, ``"test_shape"``, ``"model_type"``,
                ``"saved_model_path"`` (``None`` if ``save_model`` is
                ``False``), ``"model"`` (the trained model instance), and
                ``"x_test"``/``"y_test"`` (the held-out test set, kept
                available for downstream evaluation).

        Raises:
            Exception: Re-raises any exception encountered during
                loading, model instantiation, training, or saving, after
                logging it.
        """
        try:
            logger.info(
                "Starting training pipeline: disease='%s', model='%s'.",
                self.disease_name,
                self.model_name,
            )

            x_train, x_test, y_train, y_test = self.load_datasets()

            model = self.get_model()
            model.fit(x_train, y_train)
            logger.info(
                "Model '%s' trained successfully for disease='%s'.",
                self.model_name,
                self.disease_name,
            )

            saved_model_path: Optional[Path] = None
            if save_model:
                saved_model_path = self.save_model(model)

            result: Dict[str, Any] = {
                "disease_name": self.disease_name,
                "model_name": self.model_name,
                "target_column": self.target_column,
                "train_shape": x_train.shape,
                "test_shape": x_test.shape,
                "model_type": type(model).__name__,
                "saved_model_path": str(saved_model_path) if saved_model_path else None,
                "model": model,
                "x_test": x_test,
                "y_test": y_test,
            }

            logger.info(
                "Training pipeline completed successfully for disease='%s', model='%s'.",
                self.disease_name,
                self.model_name,
            )
            return result
        except Exception as error:
            logger.error("Training pipeline failed: %s", error)
            raise