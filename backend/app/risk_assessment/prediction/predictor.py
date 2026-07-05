"""Prediction utilities for the Risk Assessment module.

This module provides a reusable :class:`Predictor` class that loads a
single trained model from disk, accepts raw patient feature input as a
dictionary, validates it, and returns a prediction along with a
probability score when the underlying model supports it. It contains no
disease-specific logic, no training, and no evaluation.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import joblib
import pandas as pd

from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)


class Predictor:
    """Load a trained model and generate predictions from raw feature input.

    This class is disease-agnostic and model-agnostic: it loads any
    ``joblib``-serialized scikit-learn-compatible model, accepts a
    dictionary of feature values, validates that the required features
    are present, and returns the predicted class along with a
    probability score (when available). It performs no training,
    evaluation, or preprocessing beyond basic input validation and
    DataFrame conversion.

    Attributes:
        model_path: Path to the serialized (``.pkl``) trained model.
        required_features: Optional explicit list of feature names
            expected as input. If not provided, the loader attempts to
            infer them from the model itself.
        model: The loaded model instance, populated after
            :meth:`load_model` is called.
    """

    def __init__(
        self,
        model_path: Union[str, Path],
        required_features: Optional[List[str]] = None,
    ) -> None:
        """Initialize the Predictor.

        Args:
            model_path: Path to the serialized (``.pkl``) trained model
                file, typically saved by ``TrainingPipeline`` under
                ``saved_models/``.
            required_features: Optional explicit list of feature names
                expected as input, in the exact order the model was
                trained on. If ``None``, the loaded model's
                ``feature_names_in_`` attribute (when available) is used
                for validation instead.
        """
        self.model_path: Path = Path(model_path)
        self.required_features: Optional[List[str]] = required_features
        self.model: Any = None

    def load_model(self) -> Any:
        """Load the trained model from ``model_path`` using joblib.

        Returns:
            Any: The loaded model instance.

        Raises:
            FileNotFoundError: If no file exists at ``model_path``.
            Exception: Re-raises any exception encountered while
                deserializing the model, after logging it.
        """
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
            logger.error("Failed to load model from '%s': %s", self.model_path, error)
            raise

    def _resolve_required_features(self) -> Optional[List[str]]:
        """Determine the expected feature names for validation.

        Preference order: explicitly provided ``required_features``,
        then the model's ``feature_names_in_`` attribute (populated by
        scikit-learn when trained on a DataFrame), otherwise ``None``.

        Returns:
            Optional[List[str]]: The list of expected feature names, or
            ``None`` if it cannot be determined.
        """
        if self.required_features is not None:
            return self.required_features

        if self.model is not None and hasattr(self.model, "feature_names_in_"):
            return list(self.model.feature_names_in_)

        return None


    def predict(self, input_dataframe: pd.DataFrame) -> Dict[str, Any]:
        """Generate a prediction for a single set of input features.

        Loads the model if it has not already been loaded, validates and
        converts the input, and returns the predicted class along with a
        probability score when the model supports it.

        Args:
            input_dataframe: A pandas DataFrame containing the input features.

        Returns:
            Dict[str, Any]: A dictionary with keys:
                ``"predicted_class"``: The predicted class label.
                ``"probability"``: A dictionary mapping class label to
                    predicted probability, or ``None`` if the model does
                    not support probability estimation.
                ``"positive_class_probability"``: The probability
                    associated with the highest-indexed class (commonly
                    the "positive"/at-risk class in binary
                    classification), or ``None`` if unavailable.

        Raises:
            ValueError: If the input is invalid or missing required
                features.
            Exception: Re-raises any exception encountered during
                prediction, after logging it.
        """
        try:
            if self.model is None:
                self.load_model()

            predicted_class = self.model.predict(input_dataframe)[0]

            probability_dict: Optional[Dict[str, float]] = None
            positive_class_probability: Optional[float] = None

            if hasattr(self.model, "predict_proba"):
                probabilities = self.model.predict_proba(input_dataframe)[0]
                class_labels = getattr(self.model, "classes_", range(len(probabilities)))
                probability_dict = {
                    str(label): float(probability)
                    for label, probability in zip(class_labels, probabilities)
                }
                positive_class_probability = float(probabilities[-1])
            else:
                logger.warning(
                    "Model '%s' does not support predict_proba; "
                    "returning prediction without probability.",
                    type(self.model).__name__,
                )

            result = {
                "predicted_class": predicted_class,
                "probability": probability_dict,
                "positive_class_probability": positive_class_probability,
            }

            logger.info("Prediction generated: %s", result)
            return result
        except ValueError:
            raise
        except Exception as error:
            logger.error("Prediction failed: %s", error)
            raise