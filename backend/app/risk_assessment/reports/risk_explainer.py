"""Risk explanation utilities for the Risk Assessment module.

This module provides a reusable :class:`RiskExplainer` class that
generates human-readable, generic explanations and recommendations for a
given risk level. It contains no disease-specific medical advice; all
guidance is phrased generically so it applies equally to diabetes, heart
disease, stroke, hypertension, or any other risk assessment produced by
this system.
"""

from typing import Any, Dict, List

from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)

VALID_RISK_LEVELS = {"Low", "Moderate", "High"}

RISK_LEVEL_EXPLANATIONS = {
    "Low": (
        "The model estimates a low likelihood of this condition based on the "
        "provided information. This suggests that current indicators are "
        "generally favorable, though ongoing healthy habits remain important."
    ),
    "Moderate": (
        "The model estimates a moderate likelihood of this condition based on "
        "the provided information. Some indicators suggest an elevated risk "
        "that may benefit from closer attention and monitoring."
    ),
    "High": (
        "The model estimates a high likelihood of this condition based on the "
        "provided information. This suggests significant risk indicators are "
        "present and warrant prompt attention."
    ),
}

RECOMMENDATION_TEMPLATES: Dict[str, Dict[str, List[str]]] = {
    "Low": {
        "lifestyle_modifications": [
            "Maintain a balanced diet and regular physical activity.",
            "Continue healthy sleep and stress-management habits.",
        ],
        "medical_consultation": [
            "No urgent consultation is indicated based on this result alone.",
        ],
        "follow_up_testing": [
            "Continue routine health check-ups as generally recommended for your age group.",
        ],
        "preventive_measures": [
            "Keep monitoring relevant health indicators periodically.",
            "Avoid known risk-increasing behaviors (e.g., smoking, excessive alcohol use).",
        ],
    },
    "Moderate": {
        "lifestyle_modifications": [
            "Consider adopting or reinforcing a balanced diet and regular exercise routine.",
            "Evaluate and reduce known modifiable risk factors where possible.",
        ],
        "medical_consultation": [
            "Consider scheduling a consultation with a healthcare professional to review these results.",
        ],
        "follow_up_testing": [
            "Additional or more frequent testing may help clarify current risk status.",
        ],
        "preventive_measures": [
            "Increase the frequency of relevant health monitoring.",
            "Discuss preventive strategies with a healthcare provider.",
        ],
    },
    "High": {
        "lifestyle_modifications": [
            "Prioritize significant lifestyle adjustments in consultation with a healthcare professional.",
        ],
        "medical_consultation": [
            "Prompt consultation with a qualified healthcare professional is strongly advised.",
        ],
        "follow_up_testing": [
            "Further diagnostic testing is recommended to confirm and clarify this result.",
        ],
        "preventive_measures": [
            "Close, ongoing monitoring of relevant health indicators is advised.",
            "Follow any care plan established with a healthcare provider closely.",
        ],
    },
}


class RiskExplainer:
    """Generate generic, human-readable explanations and recommendations.

    This class translates a risk level (``"Low"``, ``"Moderate"``, or
    ``"High"``) into plain-language explanations and structured
    recommendations. All content is intentionally generic and contains
    no disease-specific medical advice, so the same explainer can be
    reused across diabetes, heart disease, stroke, hypertension, or any
    other risk model produced by this system.
    """

    def _validate_risk_level(self, risk_level: str) -> str:
        """Validate that a risk level is one of the supported values.

        Args:
            risk_level: The risk level to validate.

        Returns:
            str: The validated risk level, normalized to title case.

        Raises:
            ValueError: If ``risk_level`` is not one of ``"Low"``,
                ``"Moderate"``, or ``"High"``.
        """
        normalized_level = str(risk_level).strip().capitalize()

        if normalized_level not in VALID_RISK_LEVELS:
            error_message = (
                f"Unsupported risk level '{risk_level}'. "
                f"Supported levels are: {sorted(VALID_RISK_LEVELS)}."
            )
            logger.error(error_message)
            raise ValueError(error_message)

        return normalized_level

    def explain_risk_level(self, risk_level: str) -> Dict[str, str]:
        """Generate a human-readable explanation for a given risk level.

        Args:
            risk_level: One of ``"Low"``, ``"Moderate"``, or ``"High"``.

        Returns:
            Dict[str, str]: A dictionary with keys ``"risk_level"`` and
            ``"explanation"``.

        Raises:
            ValueError: If ``risk_level`` is not supported.
        """
        normalized_level = self._validate_risk_level(risk_level)
        explanation = {
            "risk_level": normalized_level,
            "explanation": RISK_LEVEL_EXPLANATIONS[normalized_level],
        }

        logger.info("Generated explanation for risk level '%s'.", normalized_level)
        return explanation

    def generate_recommendations(self, risk_level: str) -> Dict[str, List[str]]:
        """Generate generic recommendations for a given risk level.

        Args:
            risk_level: One of ``"Low"``, ``"Moderate"``, or ``"High"``.

        Returns:
            Dict[str, List[str]]: A dictionary with keys
            ``"lifestyle_modifications"``, ``"medical_consultation"``,
            ``"follow_up_testing"``, and ``"preventive_measures"``, each
            mapping to a list of generic recommendation strings.

        Raises:
            ValueError: If ``risk_level`` is not supported.
        """
        normalized_level = self._validate_risk_level(risk_level)
        recommendations = RECOMMENDATION_TEMPLATES[normalized_level]

        logger.info("Generated recommendations for risk level '%s'.", normalized_level)
        return recommendations

    def generate_summary(
        self,
        disease_name: str,
        prediction: Any,
        confidence: float,
        risk_level: str,
    ) -> str:
        """Generate a short, generic summary sentence for an assessment.

        Args:
            disease_name: Name of the disease assessed (used only as a
                label; no disease-specific advice is generated).
            prediction: The predicted class value.
            confidence: The confidence/probability score associated with
                the prediction.
            risk_level: One of ``"Low"``, ``"Moderate"``, or ``"High"``.

        Returns:
            str: A short, human-readable summary sentence.

        Raises:
            ValueError: If ``risk_level`` is not supported.
        """
        normalized_level = self._validate_risk_level(risk_level)

        summary = (
            f"Based on the provided information, the model assessed a "
            f"'{normalized_level}' risk level for {disease_name} "
            f"(predicted class: {prediction}, confidence: {confidence:.2%})."
        )

        logger.info("Generated summary: %s", summary)
        return summary

    def generate_explanation_report(
        self,
        disease_name: str,
        prediction: Any,
        confidence: float,
        risk_level: str,
    ) -> Dict[str, Any]:
        """Generate a complete explanation report for an assessment result.

        Combines the risk-level explanation, generic recommendations, and
        a short summary into a single structured dictionary.

        Args:
            disease_name: Name of the disease assessed.
            prediction: The predicted class value.
            confidence: The confidence/probability score associated with
                the prediction.
            risk_level: One of ``"Low"``, ``"Moderate"``, or ``"High"``.

        Returns:
            Dict[str, Any]: A dictionary with keys ``"summary"``,
            ``"explanation"``, and ``"recommendations"``.

        Raises:
            ValueError: If ``risk_level`` is not supported.
            Exception: Re-raises any other exception encountered while
                generating the report, after logging it.
        """
        try:
            report = {
                "summary": self.generate_summary(disease_name, prediction, confidence, risk_level),
                "explanation": self.explain_risk_level(risk_level)["explanation"],
                "recommendations": self.generate_recommendations(risk_level),
            }
            logger.info("Explanation report generated for disease='%s'.", disease_name)
            return report
        except ValueError:
            raise
        except Exception as error:
            logger.error("Failed to generate explanation report: %s", error)
            raise