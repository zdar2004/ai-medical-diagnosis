"""End-to-end pipeline runner for the Risk Assessment module.

This module provides a reusable :class:`PipelineRunner` class and a
command-line entry point that orchestrate the complete Risk Assessment
workflow: dataset preprocessing (loading, validation, and
transformation), model training, evaluation, optional model comparison,
optional prediction, and final report generation. It contains no new
business logic of its own; it strictly composes and calls the existing
modules under ``utils/``, ``preprocessing/``, ``training/``,
``evaluation/``, ``prediction/``, and ``reports/``.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from app.risk_assessment.evaluation.compare_models import ModelComparison
from app.risk_assessment.evaluation.evaluate_model import ModelEvaluator
from app.risk_assessment.preprocessing.preprocessing_pipeline import PreprocessingPipeline
from app.risk_assessment.prediction.risk_assessor import RiskAssessmentEngine
from app.risk_assessment.reports.report_generator import ReportGenerator
from app.risk_assessment.training.train_model import TrainingPipeline
from app.risk_assessment.utils.data_loader import DataLoader
from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)

DEFAULT_SAVED_MODELS_DIR = Path("risk_assessment/saved_models")
DEFAULT_EVALUATION_REPORTS_DIR = Path("risk_assessment/reports/evaluation")
DEFAULT_FINAL_REPORTS_DIR = Path("risk_assessment/reports/generated")


class PipelineRunner:
    """Orchestrate the complete Risk Assessment pipeline end to end.

    This class composes the existing, previously implemented modules of
    the Risk Assessment system into a single reusable workflow. It does
    not reimplement any validation, preprocessing, training, evaluation,
    comparison, prediction, or reporting logic; it only calls the public
    methods already exposed by those modules, in the correct order.

    Attributes:
        dataset_path: Path to the raw input dataset CSV file.
        disease_name: Name of the disease being modeled.
        model_names: List of model names to train and evaluate.
        target_column: Name of the target column in the dataset.
        save_model: Whether trained models should be persisted to disk.
        generate_report: Whether a final report should be generated.
        predict_input_path: Optional path to a JSON file containing
            patient features for an optional prediction step.
    """

    def __init__(
        self,
        dataset_path: str,
        disease_name: str,
        model_names: List[str],
        target_column: str,
        save_model: bool = False,
        generate_report: bool = False,
        predict_input_path: Optional[str] = None,
    ) -> None:
        """Initialize the PipelineRunner.

        Args:
            dataset_path: Path to the raw input dataset CSV file.
            disease_name: Name of the disease being modeled (used for
                file organization only; no disease-specific logic is
                applied).
            model_names: List of one or more model names to train and
                evaluate (e.g., ``["random_forest"]`` or
                ``["random_forest", "logistic"]``).
            target_column: Name of the target column in the dataset.
            save_model: Whether trained models should be persisted to
                disk via ``TrainingPipeline.save_model``. Defaults to
                ``False``.
            generate_report: Whether a final structured report should be
                generated (requires a prediction to have been made).
                Defaults to ``False``.
            predict_input_path: Optional path to a JSON file containing a
                dictionary of patient feature values, used to run an
                optional prediction step. Defaults to ``None``.

        Raises:
            ValueError: If ``model_names`` is empty.
        """
        if not model_names:
            error_message = "At least one model name must be provided."
            logger.error(error_message)
            raise ValueError(error_message)

        self.dataset_path: Path = Path(dataset_path)
        self.disease_name: str = disease_name
        self.model_names: List[str] = model_names
        self.target_column: str = target_column
        self.save_model: bool = save_model
        self.generate_report: bool = generate_report
        self.predict_input_path: Optional[Path] = (
            Path(predict_input_path) if predict_input_path else None
        )

    def _infer_column_types(self, dataframe: pd.DataFrame) -> Tuple[List[str], List[str]]:
        """Infer categorical and numerical feature columns from a raw dataset.

        Object-dtype columns are treated as categorical. Numeric columns
        with more than two unique values are treated as numerical.
        Numeric columns with two or fewer unique values (e.g., binary
        flags) are excluded from both lists so that the underlying
        ``ColumnTransformer`` leaves them unchanged via its passthrough
        behavior. This keeps the runner disease-agnostic without
        requiring column configuration to be exposed on the CLI.

        Args:
            dataframe: The raw dataset, including the target column.

        Returns:
            Tuple[List[str], List[str]]: ``(categorical_columns,
            numerical_columns)``.
        """
        feature_columns = [
            column for column in dataframe.columns if column != self.target_column
        ]

        categorical_columns = [
            column
            for column in feature_columns
            if not pd.api.types.is_numeric_dtype(dataframe[column])
        ]
        numerical_columns = [
            column
            for column in feature_columns
            if pd.api.types.is_numeric_dtype(dataframe[column])
            and dataframe[column].nunique(dropna=True) > 2
        ]

        logger.info(
            "Inferred column types: categorical=%s, numerical=%s.",
            categorical_columns,
            numerical_columns,
        )
        return categorical_columns, numerical_columns

    def _run_preprocessing(self) -> Dict[str, Any]:
        """Run dataset preprocessing via the refactored PreprocessingPipeline.

        Loads the raw dataset once to infer column types, then delegates
        loading, validation, encoding, scaling, and train/test splitting
        entirely to ``PreprocessingPipeline.run()``.

        Returns:
            Dict[str, Any]: The summary dictionary produced by
            ``PreprocessingPipeline.run()``, containing (among other
            keys) ``"X_train"``, ``"X_test"``, ``"y_train"``, and
            ``"y_test"``.
        """
        logger.info("[1/8] Loading raw dataset to infer column types.")
        raw_dataframe = DataLoader(self.dataset_path).load_csv()
        categorical_columns, numerical_columns = self._infer_column_types(raw_dataframe)

        logger.info("[2/8] Validating and preprocessing dataset via PreprocessingPipeline.")
        preprocessing_pipeline = PreprocessingPipeline(
            disease_name=self.disease_name,
            dataset_path=self.dataset_path,
            target_column=self.target_column,
            categorical_columns=categorical_columns,
            numerical_columns=numerical_columns,
        )
        return preprocessing_pipeline.run()

    def _train_and_evaluate_model(
        self,
        model_name: str,
        x_train: pd.DataFrame,
        x_test: pd.DataFrame,
        y_train: pd.Series,
        y_test: pd.Series,
    ) -> Dict[str, Any]:
        """Train and evaluate a single model using existing pipeline modules.

        Uses ``TrainingPipeline``'s model instantiation and saving
        methods, and ``ModelEvaluator``'s evaluation methods, without
        reimplementing any of their logic. Training and test data are
        supplied directly (already preprocessed via the refactored
        ``PreprocessingPipeline``) rather than being reloaded and
        re-split by ``TrainingPipeline`` itself.

        Args:
            model_name: Name of the model to train and evaluate.
            x_train: Preprocessed training feature matrix.
            x_test: Preprocessed test feature matrix.
            y_train: Training target vector.
            y_test: Test target vector.

        Returns:
            Dict[str, Any]: A dictionary with keys ``"model_name"``,
            ``"training_summary"``, ``"evaluation_report"``, and
            ``"saved_model_path"`` (``None`` if the model was not
            persisted).
        """
        logger.info("[3/8] Training model '%s'.", model_name)

        processed_data_dir = Path("risk_assessment/datasets/processed") / self.disease_name

        training_pipeline = TrainingPipeline(
            disease_name=self.disease_name,
            model_name=model_name,
            target_column=self.target_column,
            processed_data_dir=processed_data_dir,
            save_directory=DEFAULT_SAVED_MODELS_DIR / self.disease_name,
        )

        model = training_pipeline.get_model()
        model.fit(x_train, y_train)

        saved_model_path: Optional[Path] = None
        if self.save_model:
            saved_model_path = training_pipeline.save_model(model)

        training_summary = {
            "disease_name": self.disease_name,
            "model_name": model_name,
            "target_column": self.target_column,
            "train_shape": x_train.shape,
            "test_shape": x_test.shape,
            "model_type": type(model).__name__,
            "saved_model_path": str(saved_model_path) if saved_model_path else None,
        }

        logger.info("[4/8] Evaluating model '%s'.", model_name)
        evaluator = ModelEvaluator(model, x_test, y_test, model_name=model_name)
        evaluation_report = evaluator.evaluate()

        evaluation_report_path = evaluator.save_report_as_json(
            evaluation_report,
            output_path=DEFAULT_EVALUATION_REPORTS_DIR
            / self.disease_name
            / f"{model_name}_evaluation.json",
        )

        return {
            "model_name": model_name,
            "training_summary": training_summary,
            "evaluation_report": evaluation_report,
            "evaluation_report_path": str(evaluation_report_path),
            "saved_model_path": str(saved_model_path) if saved_model_path else None,
        }

    def _compare_models(
        self, evaluation_results: Dict[str, Dict[str, Any]], metric: str = "accuracy"
    ) -> Optional[Dict[str, Any]]:
        """Compare evaluation results across multiple models, if applicable.

        Args:
            evaluation_results: Mapping of model name to evaluation
                report, as produced by :meth:`_train_and_evaluate_model`.
            metric: The metric used for ranking and best-model selection.
                Defaults to ``"accuracy"``.

        Returns:
            Optional[Dict[str, Any]]: The comparison report produced by
            ``ModelComparison``, or ``None`` if fewer than two models
            were evaluated.
        """
        if len(evaluation_results) < 2:
            logger.info("Only one model evaluated; skipping model comparison step.")
            return None

        logger.info("[5/8] Comparing %d models.", len(evaluation_results))
        comparison = ModelComparison(evaluation_results)
        return comparison.generate_comparison_report(metric=metric)

    def _run_prediction(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Run an optional prediction step using the RiskAssessmentEngine.

        Prediction requires that the target model was persisted to disk
        (``save_model=True``), since ``RiskAssessmentEngine`` loads
        models from the standard ``saved_models`` directory structure.

        Args:
            model_name: Name of the model to use for prediction.

        Returns:
            Optional[Dict[str, Any]]: The structured assessment result
            produced by ``RiskAssessmentEngine.assess()``, or ``None`` if
            no prediction input was provided or the model was not saved.
        """
        if self.predict_input_path is None:
            logger.info("No prediction input provided; skipping prediction step.")
            return None

        if not self.save_model:
            logger.warning(
                "Prediction requested but --save-model was not set; "
                "skipping prediction step since no model file is available on disk."
            )
            return None

        logger.info("[6/8] Generating prediction using model '%s'.", model_name)

        with open(self.predict_input_path, "r", encoding="utf-8") as input_file:
            patient_features = json.load(input_file)

        engine = RiskAssessmentEngine(saved_models_dir=DEFAULT_SAVED_MODELS_DIR)
        return engine.assess(
            disease_name=self.disease_name,
            model_name=model_name,
            patient_features=patient_features,
        )

    def _generate_final_report(self, assessment_result: Optional[Dict[str, Any]]) -> Optional[Path]:
        """Generate and save a final report, if a prediction was made.

        Args:
            assessment_result: The structured assessment result produced
                by :meth:`_run_prediction`, or ``None`` if no prediction
                was made.

        Returns:
            Optional[Path]: The path to the saved report file, or
            ``None`` if report generation was skipped.
        """
        if not self.generate_report:
            logger.info("Report generation not requested; skipping.")
            return None

        if assessment_result is None:
            logger.warning(
                "Report generation requested but no prediction was made; "
                "skipping report generation since a prediction result is required."
            )
            return None

        logger.info("[7/8] Generating final report.")
        report_generator = ReportGenerator(
            reports_dir=DEFAULT_FINAL_REPORTS_DIR / self.disease_name
        )
        report = report_generator.generate_report(assessment_result)
        return report_generator.save_report_json(
            report, file_name=f"{self.disease_name}_{assessment_result['model']}_report.json"
        )

    def run(self) -> Dict[str, Any]:
        """Execute the complete Risk Assessment pipeline end to end.

        Steps executed, in order: dataset preprocessing (loading,
        validation, and transformation via ``PreprocessingPipeline``),
        training, evaluation, optional model comparison, optional
        prediction, optional final report generation. Trained models are
        saved when requested.

        Returns:
            Dict[str, Any]: A final execution summary dictionary with
            keys: ``"dataset_name"``, ``"disease"``, ``"selected_models"``,
            ``"training_status"``, ``"evaluation_status"``,
            ``"saved_model_paths"``, ``"generated_report_path"``,
            ``"best_model"``, ``"execution_time_seconds"``.

        Raises:
            Exception: Re-raises any exception encountered during
                pipeline execution, after logging it.
        """
        start_time = time.time()
        training_status = "not_started"
        evaluation_status = "not_started"
        generated_report_path: Optional[Path] = None
        saved_model_paths: Dict[str, Optional[str]] = {}

        try:
            logger.info(
                "Starting Risk Assessment pipeline for disease='%s', models=%s.",
                self.disease_name,
                self.model_names,
            )

            preprocessing_summary = self._run_preprocessing()
            x_train = preprocessing_summary["X_train"]
            x_test = preprocessing_summary["X_test"]
            y_train = preprocessing_summary["y_train"]
            y_test = preprocessing_summary["y_test"]

            evaluation_results: Dict[str, Dict[str, Any]] = {}
            model_run_details: Dict[str, Dict[str, Any]] = {}

            for model_name in self.model_names:
                result = self._train_and_evaluate_model(
                    model_name, x_train, x_test, y_train, y_test
                )
                model_run_details[model_name] = result
                evaluation_results[model_name] = result["evaluation_report"]
                saved_model_paths[model_name] = result["saved_model_path"]

            training_status = "completed"
            evaluation_status = "completed"

            comparison_report = self._compare_models(evaluation_results)
            best_model_name = (
                comparison_report["best_model"]["model_name"]
                if comparison_report is not None
                else self.model_names[0]
            )

            assessment_result = self._run_prediction(best_model_name)
            generated_report_path = self._generate_final_report(assessment_result)

            execution_time = round(time.time() - start_time, 4)

            summary: Dict[str, Any] = {
                "dataset_name": self.dataset_path.name,
                "disease": self.disease_name,
                "selected_models": self.model_names,
                "best_model": best_model_name,
                "training_status": training_status,
                "evaluation_status": evaluation_status,
                "saved_model_paths": saved_model_paths,
                "generated_report_path": str(generated_report_path) if generated_report_path else None,
                "execution_time_seconds": execution_time,
            }

            logger.info("[8/8] Pipeline execution completed: %s", summary)
            return summary
        except Exception as error:
            logger.error("Pipeline execution failed: %s", error)
            raise


def parse_arguments(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments for the pipeline runner.

    Args:
        argv: Optional list of argument strings to parse. If ``None``,
            arguments are read from ``sys.argv``.

    Returns:
        argparse.Namespace: The parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Run the complete MediSys Risk Assessment pipeline."
    )
    parser.add_argument(
        "--dataset", required=True, type=str, help="Path to the raw input dataset CSV file."
    )
    parser.add_argument(
        "--disease", required=True, type=str, help="Name of the disease being modeled."
    )
    parser.add_argument(
        "--model",
        required=True,
        type=str,
        help=(
            "Name of the model to train, or a comma-separated list of model "
            "names to train and compare (e.g. 'random_forest,logistic')."
        ),
    )
    parser.add_argument(
        "--target", required=True, type=str, help="Name of the target column in the dataset."
    )
    parser.add_argument(
        "--save-model",
        action="store_true",
        help="Persist trained model(s) to disk under saved_models/.",
    )
    parser.add_argument(
        "--generate-report",
        action="store_true",
        help="Generate a final structured report (requires --predict).",
    )
    parser.add_argument(
        "--predict",
        type=str,
        default=None,
        help="Path to a JSON file containing patient feature values for an optional prediction step.",
    )

    return parser.parse_args(argv)


def display_summary(summary: Dict[str, Any]) -> None:
    """Print a human-readable final execution summary to the console.

    Args:
        summary: The execution summary dictionary produced by
            ``PipelineRunner.run()``.
    """
    print("\n===== Risk Assessment Pipeline Execution Summary =====")
    print(f"Dataset Name       : {summary['dataset_name']}")
    print(f"Disease            : {summary['disease']}")
    print(f"Selected Model(s)  : {', '.join(summary['selected_models'])}")
    print(f"Best Model         : {summary['best_model']}")
    print(f"Training Status    : {summary['training_status']}")
    print(f"Evaluation Status  : {summary['evaluation_status']}")
    print(f"Saved Model Path(s): {summary['saved_model_paths']}")
    print(f"Generated Report   : {summary['generated_report_path']}")
    print(f"Execution Time (s) : {summary['execution_time_seconds']}")
    print("========================================================\n")


def main(argv: Optional[List[str]] = None) -> None:
    """Command-line entry point for running the Risk Assessment pipeline.

    Args:
        argv: Optional list of argument strings to parse. If ``None``,
            arguments are read from ``sys.argv``.
    """
    args = parse_arguments(argv)
    model_names = [name.strip() for name in args.model.split(",") if name.strip()]

    try:
        runner = PipelineRunner(
            dataset_path=args.dataset,
            disease_name=args.disease,
            model_names=model_names,
            target_column=args.target,
            save_model=args.save_model,
            generate_report=args.generate_report,
            predict_input_path=args.predict,
        )
        summary = runner.run()
        display_summary(summary)
    except Exception as error:
        logger.error("Pipeline run aborted due to an error: %s", error)
        sys.exit(1)


if __name__ == "__main__":
    main()