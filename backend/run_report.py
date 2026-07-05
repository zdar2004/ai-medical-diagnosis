from app.risk_assessment.prediction.risk_assessor import RiskAssessmentEngine
from app.risk_assessment.reports.report_generator import ReportGenerator

engine = RiskAssessmentEngine()

patient = {
    "gender": "Male",
    "age": 50,
    "hypertension": 1,
    "heart_disease": 0,
    "smoking_history": "former",
    "bmi": 30.2,
    "HbA1c_level": 6.8,
    "blood_glucose_level": 180,
}

assessment = engine.assess(
    disease_name="diabetes",
    model_name="logistic",
    patient_features=patient,
)

generator = ReportGenerator()

report = generator.generate_report(assessment)

saved_path = generator.save_report_json(
    report=report,
    output_path="risk_assessment/reports/generated/diabetes",
    file_name="diabetes_report.json",
)

print("=" * 60)
print("REPORT GENERATED")
print("=" * 60)
print(report)
print()
print("Saved to:")
print(saved_path)