from app.risk_assessment.prediction.risk_assessor import RiskAssessmentEngine

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

result = engine.assess(
    disease_name="heart_disease",
    model_name="logistic",
    patient_features=patient_features,
)

print(result)