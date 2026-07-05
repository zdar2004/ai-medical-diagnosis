import joblib
import pandas as pd

from app.risk_assessment.evaluation.evaluate_model import ModelEvaluator

MODEL_PATH = "risk_assessment/saved_models/diabetes/diabetes_logistic.pkl"

X_TEST_PATH = "risk_assessment/datasets/processed/diabetes/X_test.csv"
Y_TEST_PATH = "risk_assessment/datasets/processed/diabetes/y_test.csv"

REPORT_PATH = (
    "risk_assessment/reports/evaluation/diabetes/logistic_evaluation.json"
)

model = joblib.load(MODEL_PATH)

x_test = pd.read_csv(X_TEST_PATH)
y_test = pd.read_csv(Y_TEST_PATH).iloc[:, 0]

evaluator = ModelEvaluator(
    model=model,
    x_test=x_test,
    y_test=y_test,
    model_name="logistic",
)

report = evaluator.evaluate()

evaluator.save_report_as_json(
    report=report,
    output_path=REPORT_PATH,
)

print("=" * 60)
print("EVALUATION COMPLETED")
print("=" * 60)
print(f"Accuracy : {report['accuracy']:.4f}")
print(f"Precision: {report['precision']:.4f}")
print(f"Recall   : {report['recall']:.4f}")
print(f"F1 Score : {report['f1_score']:.4f}")
print(f"ROC AUC  : {report['roc_auc']:.4f}" if report["roc_auc"] is not None else "ROC AUC  : N/A")
print(REPORT_PATH)