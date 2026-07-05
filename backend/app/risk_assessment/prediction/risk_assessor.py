"""Risk assessment engine for the Risk Assessment module.

This module provides a reusable :class:`RiskAssessmentEngine` class that
ties together model loading and prediction (via :class:`Predictor`) with
confidence calculation and risk-level classification. It contains no
disease-specific logic and works identically for diabetes, heart
disease, stroke, hypertension, or any other binary-classification risk
model.
"""
import joblib
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from app.risk_assessment.prediction.predictor import Predictor
from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)

DEFAULT_SAVED_MODELS_DIR = Path("risk_assessment/saved_models")

LOW_RISK_THRESHOLD = 0.33
HIGH_RISK_THRESHOLD = 0.66

RISK_LEVEL_LOW = "Low"
RISK_LEVEL_MODERATE = "Moderate"
RISK_LEVEL_HIGH = "High"


class RiskAssessmentEngine:
    """Run end-to-end risk assessment for any supported disease and model.

    This class accepts a disease name, a model name, and a dictionary of
    patient features, then internally loads the corresponding trained
    model, performs a prediction, calculates a confidence score, and
    classifies the result into a risk level (``Low``, ``Moderate``, or
    ``High``). It contains no disease-specific branching logic: the same
    code path is used for diabetes, heart disease, stroke, hypertension,
    or any other dataset trained through the same pipeline.

    Attributes:
        saved_models_dir: Root directory containing trained model files,
            organized by disease subfolder.
    """

    def __init__(
        self, saved_models_dir: Union[str, Path] = DEFAULT_SAVED_MODELS_DIR
    ) -> None:
        """Initialize the RiskAssessmentEngine.

        Args:
            saved_models_dir: Root directory containing trained model
                files, organized as
                ``{saved_models_dir}/{disease_name}/{disease_name}_{model_name}.pkl``.
                Defaults to ``risk_assessment/saved_models``.
        """
        self.saved_models_dir: Path = Path(saved_models_dir)

    def _resolve_model_path(self, disease_name: str, model_name: str) -> Path:
        """Resolve the file path of a trained model for a given disease.

        Args:
            disease_name: Name of the disease (e.g., ``"diabetes"``).
            model_name: Name of the model (e.g., ``"random_forest"``).

        Returns:
            Path: The resolved path to the expected model file.

        Raises:
            FileNotFoundError: If no model file exists at the resolved
                path.
        """
        model_path = self.saved_models_dir / disease_name / f"{disease_name}_{model_name}.pkl"

        if not model_path.is_file():
            error_message = f"No trained model found for disease='{disease_name}', model='{model_name}' at {model_path}"
            logger.error(error_message)
            raise FileNotFoundError(error_message)

        logger.info("Resolved model path: %s", model_path.resolve())
        return model_path
    
    def _resolve_preprocessing_pipeline_path(self, disease_name: str) -> Path:
        """Resolve preprocessing pipeline path."""

        pipeline_path = (
            self.saved_models_dir
            / disease_name
            / f"{disease_name}_preprocessing_pipeline.pkl"
        )

        if not pipeline_path.is_file():
            raise FileNotFoundError(
                f"Preprocessing pipeline not found: {pipeline_path}"
            )

        logger.info(
            "Resolved preprocessing pipeline: %s",
            pipeline_path.resolve(),
        )

        return pipeline_path
    
    def _load_preprocessing_pipeline(self, disease_name: str) -> Any:
        """Load the preprocessing pipeline for a disease."""

        pipeline_path = self._resolve_preprocessing_pipeline_path(disease_name)

        try:
            preprocessing_pipeline = joblib.load(pipeline_path)

            logger.info(
                "Loaded preprocessing pipeline for disease='%s'.",
                disease_name,
            )

            return preprocessing_pipeline

        except Exception as error:
            logger.error(
                "Failed to load preprocessing pipeline: %s",
                error,
            )
            raise

    def _prepare_input(
        self,
        preprocessing_pipeline: Any,
        patient_features: Dict[str, Any],
    ) -> pd.DataFrame:
        """Transform raw patient features using the saved preprocessing pipeline."""

        input_dataframe = pd.DataFrame([patient_features])

        transformed_data = preprocessing_pipeline.transform(input_dataframe)

        if hasattr(preprocessing_pipeline, "get_feature_names_out"):
            columns = preprocessing_pipeline.get_feature_names_out()
            transformed_dataframe = pd.DataFrame(
                transformed_data,
                columns=columns,
            )
        else:
            transformed_dataframe = pd.DataFrame(transformed_data)

        logger.info(
            "Prepared transformed input with shape=%s.",
            transformed_dataframe.shape,
        )

        return transformed_dataframe

    def _calculate_confidence(self, prediction_result: Dict[str, Any]) -> float:
        """Derive a single confidence score from a prediction result.

        Preference order: the positive-class probability produced by the
        model (when available), otherwise a binary fallback confidence
        of ``1.0`` (no probability information available, so the
        prediction is treated as fully confident in its discrete
        output).

        Args:
            prediction_result: The dictionary returned by
                ``Predictor.predict()``.

        Returns:
            float: A confidence score between ``0.0`` and ``1.0``.
        """
        positive_probability = prediction_result.get("positive_class_probability")

        if positive_probability is not None:
            logger.info("Confidence derived from model probability: %.4f", positive_probability)
            return float(positive_probability)

        logger.warning(
            "No probability available from model; falling back to a default confidence of 1.0."
        )
        return 1.0

    def _classify_risk_level(self, confidence: float) -> str:
        """Classify a confidence score into a risk level category.

        Args:
            confidence: A confidence/probability score between ``0.0``
                and ``1.0``, representing the likelihood of the
                positive (at-risk) outcome.

        Returns:
            str: One of ``"Low"``, ``"Moderate"``, or ``"High"``.

        Raises:
            ValueError: If ``confidence`` is not between 0 and 1.
        """
        if not 0.0 <= confidence <= 1.0:
            error_message = f"confidence must be between 0 and 1, got {confidence}."
            logger.error(error_message)
            raise ValueError(error_message)

        if confidence < LOW_RISK_THRESHOLD:
            risk_level = RISK_LEVEL_LOW
        elif confidence < HIGH_RISK_THRESHOLD:
            risk_level = RISK_LEVEL_MODERATE
        else:
            risk_level = RISK_LEVEL_HIGH

        logger.info("Risk level classified as '%s' for confidence=%.4f", risk_level, confidence)
        return risk_level

    def assess(
        self,
        disease_name: str,
        model_name: str,
        patient_features: Dict[str, Any],
        required_features: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Run a full risk assessment for a given disease, model, and patient.

        Args:
            disease_name: Name of the disease to assess (e.g.,
                ``"diabetes"``, ``"heart_disease"``, ``"stroke"``,
                ``"hypertension"``). Used only to locate the correct
                trained model; no disease-specific logic is applied.
            model_name: Name of the trained model to use (e.g.,
                ``"random_forest"``).
            patient_features: Dictionary of feature name to feature value
                representing a single patient's input data.
            required_features: Optional explicit list of expected
                feature names, passed through to :class:`Predictor` for
                input validation.

        Returns:
            Dict[str, Any]: A structured result dictionary with keys:
                ``"disease"``, ``"prediction"``, ``"confidence"``,
                ``"risk_level"``, ``"model"``, ``"timestamp"``.

        Raises:
            FileNotFoundError: If no trained model exists for the given
                disease and model name.
            ValueError: If ``patient_features`` is invalid or missing
                required features.
            Exception: Re-raises any exception encountered during
                prediction, after logging it.
        """
        try:
            logger.info(
                "Starting risk assessment: disease='%s', model='%s'.",
                disease_name,
                model_name,
            )

            preprocessing_pipeline = self._load_preprocessing_pipeline(
                disease_name
            )

            processed_input = self._prepare_input(
                preprocessing_pipeline,
                patient_features,
            )

            model_path = self._resolve_model_path(
                disease_name,
                model_name,
            )

            predictor = Predictor(
                model_path=model_path
            )

            prediction_result = predictor.predict(
                processed_input
            )
            confidence = self._calculate_confidence(prediction_result)
            risk_level = self._classify_risk_level(confidence)

            assessment: Dict[str, Any] = {
                "disease": disease_name,
                "prediction": prediction_result["predicted_class"],
                "confidence": confidence,
                "risk_level": risk_level,
                "model": model_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            logger.info("Risk assessment completed: %s", assessment)
            return assessment
        except (FileNotFoundError, ValueError):
            raise
        except Exception as error:
            logger.error("Risk assessment failed for disease='%s': %s", disease_name, error)
            raise