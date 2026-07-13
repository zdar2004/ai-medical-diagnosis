"""
Evaluation pipeline for the Risk Assessment module.

This module provides a reusable evaluation pipeline responsible for
loading trained models, loading processed datasets, generating
predictions, computing evaluation metrics, and producing evaluation
reports.

The pipeline is completely disease-agnostic and model-agnostic.
"""

from __future__ import annotations

import joblib

from pathlib import Path
from typing import Any, Dict, Union

import pandas as pd

from app.risk_assessment.evaluation.evaluate_model import ModelEvaluator
from app.risk_assessment.evaluation.metrics import EvaluationMetrics
from app.risk_assessment.evaluation.report_generator import (
    EvaluationReportGenerator,
)
from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)

DEFAULT_DATASET_DIRECTORY = Path(
    "risk_assessment/datasets/processed"
)

DEFAULT_MODEL_DIRECTORY = Path(
    "risk_assessment/saved_models"
)

class EvaluationPipeline:
    """
    Execute the complete evaluation workflow.

    Workflow

        Load trained model
                ↓
        Load processed test dataset
                ↓
        Generate predictions
                ↓
        Compute evaluation metrics
                ↓
        Generate evaluation report

    This class contains no disease-specific logic.
    """

    def __init__(
        self,
        dataset_directory: Union[str, Path] = DEFAULT_DATASET_DIRECTORY,
        model_directory: Union[str, Path] = DEFAULT_MODEL_DIRECTORY,
    ) -> None:
        """
        Initialize the evaluation pipeline.

        Args:
            dataset_directory:
                Root directory containing processed datasets.

            model_directory:
                Root directory containing trained models.
        """

        self.dataset_directory = Path(
            dataset_directory
        )

        self.model_directory = Path(
            model_directory
        )

        self.metrics = EvaluationMetrics()

        self.report_generator = (
            EvaluationReportGenerator()
        )


    def _resolve_model_path(
        self,
        disease_name: str,
        model_name: str,
    ) -> Path:
        """
        Resolve the trained model path.

        Args:
            disease_name:
                Disease identifier.

            model_name:
                Trained model identifier.

        Returns:
            Absolute model path.

        Raises:
            FileNotFoundError:
                If the model does not exist.
        """

        model_path = (
            self.model_directory
            / disease_name
            / f"{disease_name}_{model_name}.pkl"
        )

        if not model_path.is_file():
            raise FileNotFoundError(
                f"Model not found: {model_path}"
            )

        logger.info(
            "Resolved model path: %s",
            model_path.resolve(),
        )

        return model_path
    def _resolve_dataset_directory(
        self,
        disease_name: str,
    ) -> Path:
        """
        Resolve the processed dataset directory.

        Args:
            disease_name:
                Disease identifier.

        Returns:
            Processed dataset directory.

        Raises:
            FileNotFoundError:
                If the directory does not exist.
        """

        dataset_directory = (
            self.dataset_directory
            / disease_name
        )

        if not dataset_directory.is_dir():
            raise FileNotFoundError(
                f"Processed dataset directory not found: "
                f"{dataset_directory}"
            )

        logger.info(
            "Resolved dataset directory: %s",
            dataset_directory.resolve(),
        )

        return dataset_directory
    
    def _load_model(
        self,
        disease_name: str,
        model_name: str,
    ) -> Any:
        """
        Load a trained model.

        Args:
            disease_name:
                Disease identifier.

            model_name:
                Model identifier.

        Returns:
            Loaded sklearn model.
        """

        model_path = self._resolve_model_path(
            disease_name,
            model_name,
        )

        model = joblib.load(model_path)

        logger.info(
            "Loaded model '%s'.",
            type(model).__name__,
        )

        return model
    
    def _load_processed_dataset(
        self,
        disease_name: str,
    ) -> Dict[str, Union[pd.DataFrame, pd.Series]]:
        """
        Load processed evaluation datasets.

        Args:
            disease_name:
                Disease identifier.

        Returns:
            Dictionary containing X_test and y_test.
        """

        dataset_directory = (
            self._resolve_dataset_directory(
                disease_name
            )
        )

        x_test = pd.read_csv(
            dataset_directory / "X_test.csv"
        )

        y_test = (
            pd.read_csv(
                dataset_directory / "y_test.csv"
            )
            .iloc[:, 0]
        )

        logger.info(
            "Loaded processed datasets. "
            "X_test=%s, y_test=%s",
            x_test.shape,
            y_test.shape,
        )

        return {
            "X_test": x_test,
            "y_test": y_test,
        }
    
    def _evaluate_model(
        self,
        model: Any,
        x_test: pd.DataFrame,
        y_test: pd.Series,
        model_name: str,
    ) -> Dict[str, Any]:
        """
        Evaluate a trained model on the processed test dataset.
        """

        logger.info(
            "Starting evaluation for model '%s'.",
            model_name,
        )

        evaluator = ModelEvaluator(
            model=model,
            x_test=x_test,
            y_test=y_test,
            model_name=model_name,
        )

        evaluation_result = evaluator.evaluate()

        logger.info(
            "Evaluation completed for model '%s'.",
            model_name,
        )

        return evaluation_result
    
    def _build_report(
        self,
        disease_name: str,
        model_name: str,
        evaluation_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate the final evaluation report.

        Args:
            disease_name:
                Disease identifier.

            model_name:
                Trained model identifier.

            evaluation_result:
                Metrics returned by EvaluateModel.

        Returns:
            Dictionary containing the report and saved report path.
        """

        logger.info(
            "Generating evaluation report."
        )

        report = self.report_generator.generate_report(
            disease_name=disease_name,
            model_name=model_name,
            evaluation_result=evaluation_result,
        )

        logger.info(
            "Evaluation report generated successfully."
        )

        return report
    
    def run(
        self,
        disease_name: str,
        model_name: str,
    ) -> Dict[str, Any]:
        """
        Execute the complete evaluation pipeline.

        Workflow

            Load model
                ↓
            Load processed datasets
                ↓
            Evaluate model
                ↓
            Generate report
                ↓
            Return results

        Args:
            disease_name:
                Disease identifier.

            model_name:
                Trained model identifier.

        Returns:
            Dictionary containing:

            - evaluation
            - report
            - report_path

        Raises:
            FileNotFoundError:
                If the model or processed datasets do not exist.

            Exception:
                Re-raises unexpected evaluation errors after logging.
        """

        try:
            logger.info(
                "Starting evaluation pipeline for disease='%s', model='%s'.",
                disease_name,
                model_name,
            )

            model = self._load_model(
                disease_name=disease_name,
                model_name=model_name,
            )

            dataset_bundle = self._load_processed_dataset(
                disease_name=disease_name,
            )

            evaluation_result = self._evaluate_model(
                model=model,
                x_test=dataset_bundle["X_test"],
                y_test=dataset_bundle["y_test"],
                model_name=model_name,
            )

            report_bundle = self._build_report(
                disease_name=disease_name,
                model_name=model_name,
                evaluation_result=evaluation_result,
            )

            result = {
                "evaluation": evaluation_result,
                "report": report_bundle["report"],
                "report_path": report_bundle["report_path"],
            }

            logger.info(
                "Evaluation pipeline completed successfully."
            )

            return result

        except Exception as error:
            logger.exception(
                "Evaluation pipeline failed: %s",
                error,
            )
            raise
    

