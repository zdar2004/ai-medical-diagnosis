from pydantic import BaseModel, Field


class HeartDiseaseAssessmentRequest(BaseModel):
    age: int = Field(..., ge=1, le=120)
    sex: int = Field(..., ge=0, le=1)
    cp: int = Field(..., ge=0, le=3)
    trestbps: int = Field(..., gt=0)
    chol: int = Field(..., gt=0)
    fbs: int = Field(..., ge=0, le=1)
    restecg: int = Field(..., ge=0, le=2)
    thalach: int = Field(..., gt=0)
    exang: int = Field(..., ge=0, le=1)
    oldpeak: float
    slope: int = Field(..., ge=0, le=2)
    ca: int = Field(..., ge=0, le=4)
    thal: int = Field(..., ge=0, le=3)


class DiabetesAssessmentRequest(BaseModel):
    gender: str
    age: float = Field(..., ge=0, le=120)
    hypertension: int = Field(..., ge=0, le=1)
    heart_disease: int = Field(..., ge=0, le=1)
    smoking_history: str
    bmi: float = Field(..., ge=0)
    HbA1c_level: float = Field(..., ge=0)
    blood_glucose_level: int = Field(..., ge=0)

class StrokeAssessmentRequest(BaseModel):
    gender: str
    age: float = Field(..., ge=0, le=120)
    hypertension: int = Field(..., ge=0, le=1)
    heart_disease: int = Field(..., ge=0, le=1)
    ever_married: str
    work_type: str
    Residence_type: str
    avg_glucose_level: float = Field(..., ge=0)
    bmi: float = Field(..., ge=0)
    smoking_status: str

class HypertensionAssessmentRequest(BaseModel):
    Age: int
    Salt_Intake: float
    Stress_Score: int
    BP_History: str
    Sleep_Duration: float
    BMI: float
    Medication: str | None = None
    Family_History: str
    Exercise_Level: str
    Smoking_Status: str

class RiskAssessmentResponse(BaseModel):
    disease: str
    prediction: int
    confidence: float
    risk_level: str
    model: str
    timestamp: str