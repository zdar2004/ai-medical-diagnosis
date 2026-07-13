from app.risk_assessment.prediction.risk_assessor import RiskAssessmentEngine
from app.risk_assessment.reports.report_generator import ReportGenerator

patient_features = {
    "age": 63,
    "sex": 1,
    "cp": 3,
    "trestbps": 145,
    "chol": 233,
    "fbs": 1,
    "restecg": 0,
    "thalach": 150,
    "exang": 0,
    "oldpeak": 2.3,
    "slope": 0,
    "ca": 0,
    "thal": 1,
}

engine = RiskAssessmentEngine()

assessment = engine.assess(
    disease_name="heart_disease",
    model_name="logistic",
    patient_features=patient_features,
)

print("\nAssessment Result:")
print(assessment)

generator = ReportGenerator()

report = generator.generate_report(assessment)

print("\nGenerated Report:")
print(report)

saved_path = generator.save_report_json(report)

print("\nReport saved at:")
print(saved_path)