"""Report generation utilities for the Risk Assessment module.

This module provides a reusable :class:`ReportGenerator` class that
takes a prediction result produced by ``RiskAssessmentEngine`` and turns
it into a structured, human-readable report, using
:class:`RiskExplainer` to generate the summary and recommendations. It
also provides methods to save and load reports as JSON files via
``pathlib``. It contains no model training, evaluation, or prediction
logic of its own.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

from app.risk_assessment.reports.risk_explainer import RiskExplainer
from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)

DEFAULT_REPORTS_DIR = Path("risk_assessment/reports/generated")

REQUIRED_ASSESSMENT_KEYS = {"disease", "prediction", "confidence", "risk_level", "model", "timestamp"}


class ReportGenerator:
    """Generate, save, and load structured risk assessment reports.

    This class consumes the structured result produced by
    ``RiskAssessmentEngine.assess()`` and enriches it with a
    human-readable summary and generic recommendations (via
    :class:`RiskExplainer`), producing a single report dictionary. It
    contains no disease-specific logic, no prediction logic, and no
    model-related logic of its own.

    Attributes:
        reports_dir: Default directory used when saving reports without
            an explicit output path.
        explainer: The :class:`RiskExplainer` instance used to generate
            summaries and recommendations.
    """

    def __init__(
        self,
        reports_dir: Union[str, Path] = DEFAULT_REPORTS_DIR,
        explainer: Optional[RiskExplainer] = None,
    ) -> None:
        """Initialize the ReportGenerator.

        Args:
            reports_dir: Default directory used when saving reports
                without an explicit output path. Defaults to
                ``risk_assessment/reports/generated``.
            explainer: Optional :class:`RiskExplainer` instance to use.
                If ``None``, a new default instance is created.
        """
        self.reports_dir: Path = Path(reports_dir)
        self.explainer: RiskExplainer = explainer if explainer is not None else RiskExplainer()

    def _validate_assessment_result(self, assessment_result: Dict[str, Any]) -> None:
        """Validate that an assessment result contains the required keys.

        Args:
            assessment_result: The prediction result dictionary produced
                by ``RiskAssessmentEngine.assess()``.

        Raises:
            TypeError: If ``assessment_result`` is not a dictionary.
            ValueError: If any required key is missing from
                ``assessment_result``.
        """
        if not isinstance(assessment_result, dict):
            error_message = (
                f"assessment_result must be a dict, got {type(assessment_result).__name__}."
            )
            logger.error(error_message)
            raise TypeError(error_message)

        missing_keys = REQUIRED_ASSESSMENT_KEYS - assessment_result.keys()
        if missing_keys:
            error_message = f"assessment_result is missing required key(s): {sorted(missing_keys)}"
            logger.error(error_message)
            raise ValueError(error_message)

    def generate_report(self, assessment_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a structured report from a risk assessment result.

        Args:
            assessment_result: The prediction result dictionary produced
                by ``RiskAssessmentEngine.assess()``, expected to contain
                the keys ``"disease"``, ``"prediction"``, ``"confidence"``,
                ``"risk_level"``, ``"model"``, and ``"timestamp"``.

        Returns:
            Dict[str, Any]: A structured report dictionary with keys:
                ``"disease"``, ``"prediction"``, ``"confidence"``,
                ``"risk_level"``, ``"model_used"``, ``"timestamp"``,
                ``"summary"``, ``"recommendations"``.

        Raises:
            TypeError: If ``assessment_result`` is not a dictionary.
            ValueError: If required keys are missing from
                ``assessment_result`` or if ``risk_level`` is not
                supported by :class:`RiskExplainer`.
            Exception: Re-raises any other exception encountered while
                generating the report, after logging it.
        """
        try:
            self._validate_assessment_result(assessment_result)

            disease = assessment_result["disease"]
            prediction = assessment_result["prediction"]
            confidence = assessment_result["confidence"]
            risk_level = assessment_result["risk_level"]
            model_used = assessment_result["model"]
            timestamp = assessment_result["timestamp"]

            explanation_report = self.explainer.generate_explanation_report(
                disease_name=disease,
                prediction=prediction,
                confidence=confidence,
                risk_level=risk_level,
            )

            report: Dict[str, Any] = {
                "disease": disease,
                "prediction": prediction,
                "confidence": confidence,
                "risk_level": risk_level,
                "model_used": model_used,
                "timestamp": timestamp,
                "summary": explanation_report["summary"],
                "recommendations": explanation_report["recommendations"],
            }

            logger.info("Report generated for disease='%s'.", disease)
            return report
        except (TypeError, ValueError):
            raise
        except Exception as error:
            logger.error("Failed to generate report: %s", error)
            raise

    def save_report_json(
        self,
        report: Dict[str, Any],
        output_path: Union[str, Path] = None,
        file_name: str = "risk_report.json",
    ) -> Path:
        """Save a report dictionary to a JSON file.

        Args:
            report: The report dictionary to save (typically the output
                of :meth:`generate_report`).
            output_path: Directory in which to save the report. Defaults
                to ``self.reports_dir`` if not provided.
            file_name: Name of the output JSON file. Defaults to
                ``"risk_report.json"``.

        Returns:
            Path: The resolved path where the report was saved.

        Raises:
            OSError: If the file cannot be written due to filesystem
                permission issues.
            TypeError: If the report contains values that are not
                JSON-serializable.
        """
        target_dir = Path(output_path) if output_path is not None else self.reports_dir

        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            file_path = target_dir / file_name

            with open(file_path, "w", encoding="utf-8") as json_file:
                json.dump(report, json_file, indent=4, default=str)

            logger.info("Report saved to: %s", file_path.resolve())
            return file_path
        except (OSError, TypeError) as error:
            logger.error("Failed to save report to '%s': %s", target_dir, error)
            raise

    def load_report_json(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Load a previously saved report from a JSON file.

        Args:
            file_path: Path to the JSON report file to load.

        Returns:
            Dict[str, Any]: The loaded report dictionary.

        Raises:
            FileNotFoundError: If no file exists at ``file_path``.
            json.JSONDecodeError: If the file does not contain valid
                JSON.
        """
        path = Path(file_path)

        if not path.is_file():
            error_message = f"Report file not found: {path}"
            logger.error(error_message)
            raise FileNotFoundError(error_message)

        try:
            with open(path, "r", encoding="utf-8") as json_file:
                report = json.load(json_file)

            logger.info("Report loaded from: %s", path.resolve())
            return report
        except json.JSONDecodeError as error:
            logger.error("Failed to parse report JSON at '%s': %s", path, error)
            raise