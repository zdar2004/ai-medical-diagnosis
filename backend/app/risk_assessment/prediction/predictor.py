"""Prediction utilities for the Risk Assessment module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import joblib
import pandas as pd

from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)


class Predictor:
    """Load a trained model and generate predictions from preprocessed input."""

    def __init__(
        self,
        model_path: Union[str, Path],
        required_features: Optional[List[str]] = None,
    ) -> None:
        self.model_path = Path(model_path)
        self.required_features = required_features
        self.model: Any = None

    def load_model(self) -> Any:
        """Load the trained model from disk."""

        if not self.model_path.is_file():
            error_message = f"Model file not found: {self.model_path}"
            logger.error(error_message)
            raise FileNotFoundError(error_message)

        try:
            self.model = joblib.load(self.model_path)

            logger.info(
                "Model loaded from '%s' -> %s",
                self.model_path.resolve(),
                type(self.model).__name__,
            )

            return self.model

        except Exception as error:
            logger.error(
                "Failed to load model from '%s': %s",
                self.model_path,
                error,
            )
            raise

    def _resolve_required_features(self) -> Optional[List[str]]:
        """Determine expected model feature names."""

        if self.required_features is not None:
            return self.required_features

        if self.model is not None and hasattr(
            self.model,
            "feature_names_in_",
        ):
            return list(self.model.feature_names_in_)

        return None

    def predict(
        self,
        input_dataframe: pd.DataFrame,
    ) -> Dict[str, Any]:
        """Generate prediction from already-preprocessed input."""

        try:
            if not isinstance(input_dataframe, pd.DataFrame):
                raise ValueError(
                    "input_dataframe must be a pandas DataFrame."
                )

            if input_dataframe.empty:
                raise ValueError(
                    "input_dataframe cannot be empty."
                )

            if self.model is None:
                self.load_model()

            expected_features = self._resolve_required_features()

            if expected_features is not None:
                missing_features = [
                    feature
                    for feature in expected_features
                    if feature not in input_dataframe.columns
                ]

                if missing_features:
                    raise ValueError(
                        f"Missing required model features: "
                        f"{missing_features}"
                    )

                # Ensure exact feature order expected by the model.
                input_dataframe = input_dataframe[
                    expected_features
                ]

            predicted_class = int(
                self.model.predict(input_dataframe)[0]
            )

            probability_dict: Optional[Dict[str, float]] = None
            positive_class_probability: Optional[float] = None

            if hasattr(self.model, "predict_proba"):
                probabilities = self.model.predict_proba(
                    input_dataframe
                )[0]

                class_labels = getattr(
                    self.model,
                    "classes_",
                    range(len(probabilities)),
                )

                probability_dict = {
                    str(label): float(probability)
                    for label, probability in zip(
                        class_labels,
                        probabilities,
                    )
                }

                # Binary classification:
                # probability of class 1
                if 1 in class_labels:
                    class_1_index = list(class_labels).index(1)
                    positive_class_probability = float(
                        probabilities[class_1_index]
                    )

            else:
                logger.warning(
                    "Model '%s' does not support predict_proba.",
                    type(self.model).__name__,
                )

            result = {
                "predicted_class": predicted_class,
                "probability": probability_dict,
                "positive_class_probability": (
                    positive_class_probability
                ),
            }

            logger.info(
                "Prediction generated: %s",
                result,
            )

            return result

        except ValueError:
            raise

        except Exception as error:
            logger.error(
                "Prediction failed: %s",
                error,
            )
            raise