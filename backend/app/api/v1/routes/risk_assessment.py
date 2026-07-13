from app.risk_assessment.prediction.risk_assessor import RiskAssessmentEngine
from app.schemas.risk_assessment import (
    HeartDiseaseAssessmentRequest,
    DiabetesAssessmentRequest,
    StrokeAssessmentRequest,
    HypertensionAssessmentRequest,
    RiskAssessmentResponse,
)
from fastapi import APIRouter

router = APIRouter(
    prefix="/risk-assessment",
    tags=["Risk Assessment"],
)


@router.get("/test")
async def test_risk_assessment():
    return {
        "message": "Risk Assessment API is working."
    }


@router.post(
    "/heart-disease",
    response_model=RiskAssessmentResponse,
)
async def assess_heart_disease(
    request: HeartDiseaseAssessmentRequest,
):
    engine = RiskAssessmentEngine()

    return engine.assess(
        disease_name="heart_disease",
        model_name="logistic",
        patient_features=request.model_dump(),
    )


@router.post(
    "/diabetes",
    response_model=RiskAssessmentResponse,
)
async def assess_diabetes(
    request: DiabetesAssessmentRequest,
):
    engine = RiskAssessmentEngine()

    return engine.assess(
        disease_name="diabetes",
        model_name="logistic",
        patient_features=request.model_dump(),
    )


@router.post(
    "/stroke",
    response_model=RiskAssessmentResponse,
)
async def assess_stroke(
    request: StrokeAssessmentRequest,
):
    engine = RiskAssessmentEngine()

    return engine.assess(
        disease_name="stroke",
        model_name="logistic",
        patient_features=request.model_dump(),
    )

@router.post(
    "/hypertension",
    response_model=RiskAssessmentResponse,
)
async def assess_hypertension(
    request: HypertensionAssessmentRequest,
):
    engine = RiskAssessmentEngine()

    return engine.assess(
        disease_name="hypertension",
        model_name="logistic",
        patient_features=request.model_dump(),
    )
