"""
Run model evaluation for the Risk Assessment module.

Usage:
    python run_evaluation.py
"""

from app.risk_assessment.evaluation.evaluation_pipeline import (
    EvaluationPipeline,
)


def main() -> None:
    """Run the evaluation pipeline."""

    pipeline = EvaluationPipeline()

    result = pipeline.run(
    disease_name="hypertension",
    model_name="logistic",
)

    evaluation = result["evaluation"]
    report_path = result["report_path"]

    print("=" * 60)
    print("EVALUATION COMPLETED")
    print("=" * 60)

    print(f"Accuracy : {evaluation['accuracy']:.4f}")
    print(f"Precision: {evaluation['precision']:.4f}")
    print(f"Recall   : {evaluation['recall']:.4f}")
    print(f"F1 Score : {evaluation['f1_score']:.4f}")

    if evaluation["roc_auc"] is not None:
        print(f"ROC AUC  : {evaluation['roc_auc']:.4f}")
    else:
        print("ROC AUC  : N/A")

    print()

    print("Confusion Matrix")
    print("-" * 60)
    print(evaluation["confusion_matrix"])

    print()

    print("Classification Report")
    print("-" * 60)

    for label, values in evaluation["classification_report"].items():
        print(f"{label}:")
        print(values)
        print()

    print("=" * 60)
    print(f"Report Saved : {report_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()