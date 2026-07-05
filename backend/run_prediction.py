from app.risk_assessment.prediction.risk_assessor import RiskAssessmentEngine

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

result = engine.assess(
    disease_name="diabetes",
    model_name="logistic",
    patient_features=patient,
)

print("=" * 60)
print("PREDICTION COMPLETED")
print("=" * 60)
print(result)