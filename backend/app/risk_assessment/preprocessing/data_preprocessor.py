"""Reusable, configurable tabular preprocessing for the Risk Assessment module.

This module provides a reusable :class:`DataPreprocessor` class built
around a scikit-learn :class:`~sklearn.compose.ColumnTransformer`. The
transformer configuration (which columns are categorical, which are
numerical, and which are left untouched) is supplied by the caller, so
the same class can preprocess any disease's dataset without containing
any disease-specific logic itself. It handles missing-value imputation,
categorical encoding (``OneHotEncoder``), numerical scaling
(``StandardScaler``), leaves all remaining columns (e.g., binary flags)
unchanged, performs a stratified train/test split, and persists both the
fitted transformer and the processed datasets to disk.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.risk_assessment.utils.file_utils import create_directory
from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)

DEFAULT_PROCESSED_DATA_DIR = Path("risk_assessment/datasets/processed")
DEFAULT_TEST_SIZE = 0.2
DEFAULT_RANDOM_STATE = 42


class DataPreprocessor:
    """Preprocess a tabular binary-classification dataset via a ColumnTransformer.

    This class contains no disease-specific logic. All column
    configuration (which columns should be one-hot encoded, which
    should be standardized, and which should be left unchanged) is
    supplied through the constructor, so the exact same class can be
    reused for diabetes, heart disease, stroke, hypertension, or any
    other tabular binary-classification dataset simply by passing a
    different configuration.

    Column handling:
        - ``categorical_columns``: imputed (most frequent) then encoded
          with :class:`~sklearn.preprocessing.OneHotEncoder`.
        - ``numerical_columns``: imputed (mean) then scaled with
          :class:`~sklearn.preprocessing.StandardScaler`.
        - Any remaining feature column (e.g., binary flags such as
          ``hypertension`` or ``heart_disease``) is passed through
          unchanged via the ``ColumnTransformer``'s
          ``remainder="passthrough"`` behavior.

    Attributes:
        target_column: Name of the target column used for feature/target
            separation.
        categorical_columns: List of column names to one-hot encode.
        numerical_columns: List of column names to standardize.
        test_size: Proportion of the dataset reserved for testing.
        random_state: Random seed used for the train/test split.
        column_transformer: The fitted
            :class:`~sklearn.compose.ColumnTransformer`, populated after
            :meth:`fit_transform_features` is called.
    """

    def __init__(
        self,
        target_column: str,
        categorical_columns: Optional[List[str]] = None,
        numerical_columns: Optional[List[str]] = None,
        test_size: float = DEFAULT_TEST_SIZE,
        random_state: int = DEFAULT_RANDOM_STATE,
    ) -> None:
        """Initialize the DataPreprocessor.

        Args:
            target_column: Name of the target column in the dataset.
            categorical_columns: Names of columns to impute and one-hot
                encode. Defaults to an empty list if not provided.
            numerical_columns: Names of columns to impute and
                standardize. Defaults to an empty list if not provided.
            test_size: Proportion of the dataset reserved for testing.
                Defaults to ``0.2``.
            random_state: Random seed used for the train/test split.
                Defaults to ``42``.

        Raises:
            ValueError: If ``test_size`` is not between 0 and 1
                (exclusive).
        """
        if not 0.0 < test_size < 1.0:
            error_message = f"test_size must be between 0 and 1 (exclusive), got {test_size}."
            logger.error(error_message)
            raise ValueError(error_message)

        self.target_column: str = target_column
        self.categorical_columns: List[str] = categorical_columns or []
        self.numerical_columns: List[str] = numerical_columns or []
        self.test_size: float = test_size
        self.random_state: int = random_state
        self.column_transformer: Optional[ColumnTransformer] = None

    def separate_features_and_target(
        self, dataframe: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Split a DataFrame into feature matrix (X) and target vector (y).

        Args:
            dataframe: The input DataFrame, including the target column.

        Returns:
            Tuple[pd.DataFrame, pd.Series]: A tuple ``(features, target)``
            where ``features`` excludes the target column and ``target``
            is the target column as a Series.

        Raises:
            KeyError: If the target column is not present in the
                DataFrame.
        """
        if self.target_column not in dataframe.columns:
            error_message = f"Target column '{self.target_column}' not found in dataset."
            logger.error(error_message)
            raise KeyError(error_message)

        features = dataframe.drop(columns=[self.target_column])
        target = dataframe[self.target_column]

        logger.info(
            "Separated features (shape=%s) and target '%s' (shape=%s).",
            features.shape,
            self.target_column,
            target.shape,
        )
        return features, target

    def split_dataset(
        self, features: pd.DataFrame, target: pd.Series
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """Split features and target into stratified train/test sets.

        Args:
            features: The feature matrix (X).
            target: The target vector (y).

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
            ``(X_train, X_test, y_train, y_test)``.

        Raises:
            Exception: Re-raises any exception encountered during the
                split, after logging it.
        """
        try:
            stratify = target if target.nunique() > 1 else None

            x_train, x_test, y_train, y_test = train_test_split(
                features,
                target,
                test_size=self.test_size,
                random_state=self.random_state,
                stratify=stratify,
            )

            logger.info(
                "Train/test split complete: train=%s, test=%s (test_size=%.2f, random_state=%d).",
                x_train.shape,
                x_test.shape,
                self.test_size,
                self.random_state,
            )
            return x_train, x_test, y_train, y_test
        except Exception as error:
            logger.error("Failed to split dataset: %s", error)
            raise

    def _build_column_transformer(self) -> ColumnTransformer:
        """Build the (unfitted) ColumnTransformer for this configuration.

        Categorical columns are imputed (most frequent) and one-hot
        encoded. Numerical columns are imputed (mean) and standardized.
        Any column not listed in ``categorical_columns`` or
        ``numerical_columns`` (e.g., binary flag columns) is passed
        through unchanged.

        Returns:
            ColumnTransformer: The configured, unfitted transformer.
        """
        transformers: List[Tuple[str, Pipeline, List[str]]] = []

        if self.categorical_columns:
            categorical_pipeline = Pipeline(
                steps=[
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    ("encoder", OneHotEncoder(handle_unknown="ignore")),
                ]
            )
            transformers.append(("categorical", categorical_pipeline, self.categorical_columns))

        if self.numerical_columns:
            numerical_pipeline = Pipeline(
                steps=[
                    ("imputer", SimpleImputer(strategy="mean")),
                    ("scaler", StandardScaler()),
                ]
            )
            transformers.append(("numerical", numerical_pipeline, self.numerical_columns))

        column_transformer = ColumnTransformer(transformers=transformers, remainder="passthrough")

        logger.info(
            "Built ColumnTransformer: categorical=%s, numerical=%s, remainder='passthrough'.",
            self.categorical_columns,
            self.numerical_columns,
        )
        return column_transformer

    def fit_transform_features(self, x_train: pd.DataFrame) -> pd.DataFrame:
        """Fit the ColumnTransformer on the training features and transform them.

        Args:
            x_train: The training feature matrix.

        Returns:
            pd.DataFrame: The transformed training features, with column
            names derived from the fitted transformer.

        Raises:
            Exception: Re-raises any exception encountered while fitting
                or transforming, after logging it.
        """
        try:
            self.column_transformer = self._build_column_transformer()
            transformed_array = self.column_transformer.fit_transform(x_train)
            feature_names = self.column_transformer.get_feature_names_out()

            transformed_dataframe = pd.DataFrame(
                transformed_array, columns=feature_names, index=x_train.index
            )

            logger.info(
                "Fitted ColumnTransformer and transformed training features -> shape=%s.",
                transformed_dataframe.shape,
            )
            return transformed_dataframe
        except Exception as error:
            logger.error("Failed to fit/transform training features: %s", error)
            raise

    def transform_features(self, x: pd.DataFrame) -> pd.DataFrame:
        """Transform features using an already-fitted ColumnTransformer.

        Args:
            x: The feature matrix to transform (e.g., the test set).

        Returns:
            pd.DataFrame: The transformed features, with column names
            derived from the fitted transformer.

        Raises:
            RuntimeError: If the ColumnTransformer has not been fitted
                yet (i.e., :meth:`fit_transform_features` has not been
                called).
            Exception: Re-raises any exception encountered while
                transforming, after logging it.
        """
        if self.column_transformer is None:
            error_message = (
                "ColumnTransformer has not been fitted yet. "
                "Call fit_transform_features() on the training set first."
            )
            logger.error(error_message)
            raise RuntimeError(error_message)

        try:
            transformed_array = self.column_transformer.transform(x)
            feature_names = self.column_transformer.get_feature_names_out()

            transformed_dataframe = pd.DataFrame(
                transformed_array, columns=feature_names, index=x.index
            )

            logger.info("Transformed features using fitted ColumnTransformer -> shape=%s.", transformed_dataframe.shape)
            return transformed_dataframe
        except Exception as error:
            logger.error("Failed to transform features: %s", error)
            raise

    def save_pipeline(
        self, output_path: Union[str, Path], file_name: str = "preprocessing_pipeline.pkl"
    ) -> Path:
        """Persist the fitted ColumnTransformer to disk using joblib.

        Args:
            output_path: Directory in which to save the fitted pipeline.
            file_name: Name of the output ``.pkl`` file. Defaults to
                ``"preprocessing_pipeline.pkl"``.

        Returns:
            Path: The resolved path where the fitted pipeline was saved.

        Raises:
            RuntimeError: If the ColumnTransformer has not been fitted
                yet.
            OSError: If the file cannot be written due to filesystem
                permission issues.
        """
        if self.column_transformer is None:
            error_message = "Cannot save an unfitted ColumnTransformer. Fit it first."
            logger.error(error_message)
            raise RuntimeError(error_message)

        try:
            target_dir = Path(output_path)
            create_directory(target_dir)
            file_path = target_dir / file_name

            joblib.dump(self.column_transformer, file_path)
            logger.info("Fitted preprocessing pipeline saved to: %s", file_path.resolve())
            return file_path
        except OSError as error:
            logger.error("Failed to save preprocessing pipeline to '%s': %s", output_path, error)
            raise

    def save_processed_datasets(
        self,
        x_train: pd.DataFrame,
        x_test: pd.DataFrame,
        y_train: pd.Series,
        y_test: pd.Series,
        output_dir: Union[str, Path],
    ) -> Dict[str, Path]:
        """Save processed train/test feature and target sets to CSV files.

        Args:
            x_train: Processed training feature matrix.
            x_test: Processed test feature matrix.
            y_train: Training target vector.
            y_test: Test target vector.
            output_dir: Directory in which to save the CSV files.

        Returns:
            Dict[str, Path]: A mapping of dataset name (``"X_train"``,
            ``"X_test"``, ``"y_train"``, ``"y_test"``) to the resolved
            path where it was saved.

        Raises:
            OSError: If any file cannot be written due to filesystem
                permission issues.
        """
        try:
            target_dir = Path(output_dir)
            create_directory(target_dir)

            file_paths = {
                "X_train": target_dir / "X_train.csv",
                "X_test": target_dir / "X_test.csv",
                "y_train": target_dir / "y_train.csv",
                "y_test": target_dir / "y_test.csv",
            }

            x_train.to_csv(file_paths["X_train"], index=False)
            x_test.to_csv(file_paths["X_test"], index=False)
            y_train.to_csv(file_paths["y_train"], index=False, header=[self.target_column])
            y_test.to_csv(file_paths["y_test"], index=False, header=[self.target_column])

            logger.info("Processed train/test datasets saved to: %s", target_dir.resolve())
            return file_paths
        except OSError as error:
            logger.error("Failed to save processed datasets to '%s': %s", output_dir, error)
            raise

    def run(
        self,
        dataframe: pd.DataFrame,
        pipeline_output_dir: Union[str, Path],
        processed_output_dir: Union[str, Path],
        pipeline_file_name: str = "preprocessing_pipeline.pkl",
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """Run the full preprocessing workflow end to end.

        Executes, in order: feature/target separation, stratified
        train/test split, fitting the ColumnTransformer on the training
        set, transforming both the training and test sets, saving the
        fitted transformer, and saving the processed datasets.

        Args:
            dataframe: The raw input DataFrame, including the target
                column.
            pipeline_output_dir: Directory in which to save the fitted
                ColumnTransformer.
            processed_output_dir: Directory in which to save the
                processed train/test CSV files.
            pipeline_file_name: Name of the saved pipeline ``.pkl`` file.
                Defaults to ``"preprocessing_pipeline.pkl"``.

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]: The
            processed ``(X_train, X_test, y_train, y_test)``.

        Raises:
            Exception: Re-raises any exception encountered during any
                preprocessing step, after logging it.
        """
        try:
            logger.info("Starting preprocessing run for dataset (shape=%s).", dataframe.shape)

            features, target = self.separate_features_and_target(dataframe)
            x_train_raw, x_test_raw, y_train, y_test = self.split_dataset(features, target)

            x_train_processed = self.fit_transform_features(x_train_raw)
            x_test_processed = self.transform_features(x_test_raw)

            self.save_pipeline(pipeline_output_dir, file_name=pipeline_file_name)
            self.save_processed_datasets(
                x_train_processed, x_test_processed, y_train, y_test, processed_output_dir
            )

            logger.info(
                "Preprocessing run complete: X_train=%s, X_test=%s.",
                x_train_processed.shape,
                x_test_processed.shape,
            )
            return x_train_processed, x_test_processed, y_train, y_test
        except Exception as error:
            logger.error("Preprocessing run failed: %s", error)
            raise