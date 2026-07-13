"""
Evaluation report generation utilities for the Risk Assessment module.

This module provides a reusable report generator responsible for
persisting evaluation results produced by the evaluation pipeline.

Responsibilities
----------------
* Generate structured evaluation reports.
* Save reports as JSON.
* Create output directories.
* Return report paths.

The module intentionally performs no prediction, training,
or metric calculation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Union

from app.risk_assessment.utils.file_utils import create_directory
from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)

DEFAULT_REPORT_DIRECTORY = Path(
    "risk_assessment/reports/evaluation"
)


class EvaluationReportGenerator:
    """
    Generate and persist model evaluation reports.

    This class is completely reusable and contains no disease-specific
    or model-specific logic. It simply receives an already-computed
    evaluation dictionary and stores it as a structured JSON report.

    Attributes
    ----------
    report_directory:
        Root directory where evaluation reports are stored.
    """

    def __init__(
        self,
        report_directory: Union[str, Path] = DEFAULT_REPORT_DIRECTORY,
    ) -> None:
        """
        Initialize the report generator.

        Args:
            report_directory:
                Root directory for evaluation reports.
        """

        self.report_directory = Path(report_directory)
    
    def _resolve_output_directory(
        self,
        disease_name: str,
    ) -> Path:
        """
        Resolve the output directory for a disease.

        The directory structure is:

            reports/
                evaluation/
                    disease_name/

        Args:
            disease_name:
                Disease identifier.

        Returns:
            Path to the disease-specific report directory.
        """

        output_directory = (
            self.report_directory
            / disease_name
        )

        create_directory(output_directory)

        logger.info(
            "Resolved report directory: %s",
            output_directory.resolve(),
        )

        return output_directory
    
    def _resolve_report_path(
        self,
        disease_name: str,
        model_name: str,
    ) -> Path:
        """
        Resolve the JSON report path.

        Report filename format:

            model_name_evaluation.json

        Example:

            logistic_evaluation.json

        Args:
            disease_name:
                Disease identifier.

            model_name:
                Trained model identifier.

        Returns:
            Full report file path.
        """

        output_directory = self._resolve_output_directory(
            disease_name,
        )

        report_path = (
            output_directory
            / f"{model_name}_evaluation.json"
        )

        logger.info(
            "Resolved report path: %s",
            report_path.resolve(),
        )

        return report_path
    
    def _add_metadata(
        self,
        report: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Add metadata to an evaluation report.

        The original report dictionary is copied so the caller's
        object is not modified.

        Args:
            report:
                Evaluation results.

        Returns:
            Report dictionary enriched with metadata.
        """

        report_copy = dict(report)

        report_copy["generated_at"] = (
            datetime.now(timezone.utc).isoformat()
        )

        report_copy["report_version"] = "1.0"

        logger.info(
            "Evaluation report metadata added."
        )

        return report_copy
    
    def save_json(
        self,
        report: Dict[str, Any],
        disease_name: str,
        model_name: str,
    ) -> Path:
        """
        Save an evaluation report as a JSON file.

        Args:
            report:
                Evaluation report dictionary.

            disease_name:
                Disease identifier.

            model_name:
                Trained model identifier.

        Returns:
            Path to the saved JSON report.

        Raises:
            OSError:
                If the report cannot be written.
        """

        report_path = self._resolve_report_path(
            disease_name=disease_name,
            model_name=model_name,
        )

        report_with_metadata = self._add_metadata(
            report,
        )

        try:
            with report_path.open(
                mode="w",
                encoding="utf-8",
            ) as output_file:
                json.dump(
                    report_with_metadata,
                    output_file,
                    indent=4,
                    ensure_ascii=False,
                )

            logger.info(
                "Evaluation report saved to: %s",
                report_path.resolve(),
            )

            return report_path

        except OSError as error:
            logger.error(
                "Failed to save evaluation report: %s",
                error,
            )
            raise

    def report_exists(
        self,
        disease_name: str,
        model_name: str,
    ) -> bool:
        """
        Check whether an evaluation report already exists.

        Args:
            disease_name:
                Disease identifier.

            model_name:
                Model identifier.

        Returns:
            True if the report exists, otherwise False.
        """

        report_path = self._resolve_report_path(
            disease_name=disease_name,
            model_name=model_name,
        )

        exists = report_path.exists()

        logger.info(
            "Evaluation report exists: %s",
            exists,
        )

        return exists
    
    def load_json(
        self,
        disease_name: str,
        model_name: str,
    ) -> Dict[str, Any]:
        """
        Load a previously saved evaluation report.

        Args:
            disease_name:
                Disease identifier.

            model_name:
                Model identifier.

        Returns:
            Parsed JSON report.

        Raises:
            FileNotFoundError:
                If the report does not exist.
        """

        report_path = self._resolve_report_path(
            disease_name=disease_name,
            model_name=model_name,
        )

        if not report_path.exists():
            raise FileNotFoundError(report_path)

        with report_path.open(
            mode="r",
            encoding="utf-8",
        ) as input_file:
            report = json.load(input_file)

        logger.info(
            "Loaded evaluation report from %s",
            report_path.resolve(),
        )

        return report
    
    def generate_report(
        self,
        disease_name: str,
        model_name: str,
        evaluation_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate and persist a complete evaluation report.

        This method enriches the supplied evaluation result with report
        metadata, saves it as a JSON file, and returns the final report
        together with its output path.

        Args:
            disease_name:
                Disease identifier.

            model_name:
                Trained model identifier.

            evaluation_result:
                Dictionary returned by the evaluation pipeline.

        Returns:
            Dictionary containing:

            - report
            - report_path
        """

        logger.info(
            "Generating evaluation report for disease='%s', model='%s'.",
            disease_name,
            model_name,
        )

        report = self._add_metadata(
            evaluation_result,
        )

        report_path = self.save_json(
            report=report,
            disease_name=disease_name,
            model_name=model_name,
        )

        logger.info(
            "Evaluation report generated successfully."
        )

        return {
            "report": report,
            "report_path": report_path,
        }