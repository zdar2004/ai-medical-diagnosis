from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import require_roles
from app.database import get_database
from app.models.diagnosis import DiagnosisCreate, DiagnosisResponse, DiagnosisUpdate
from app.models.user import UserInDB, UserRole
from app.services.diagnosis_service import DiagnosisService

router = APIRouter(
    prefix="/diagnoses",
    tags=["Diagnoses"],
)


def _svc(db: AsyncIOMotorDatabase = Depends(get_database)) -> DiagnosisService:
    """Inject DiagnosisService with the live DB handle."""
    return DiagnosisService(db)


# ── POST / ────────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=DiagnosisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Open a new diagnosis record",
    responses={
        400: {"description": "Invalid patient ID or patient not found"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient role"},
        422: {"description": "Validation error"},
    },
)
async def create_diagnosis(
    payload: DiagnosisCreate,
    current_user: UserInDB = Depends(
        require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.STAFF)
    ),
    svc: DiagnosisService = Depends(_svc),
) -> DiagnosisResponse:
    """
    Open a new diagnosis record for a patient.

    - **patient_id**: valid 24-character MongoDB ObjectId of an existing patient
    - **symptoms**: one or more symptoms; normalised to lowercase on storage
    - **role required**: Admin · Doctor · Staff

    AI fields (`predicted_disease`, `confidence_score`) are `null` at
    creation — they are populated when the AI prediction service runs.
    Status is set to `pending` automatically.

    The authenticated user's ID is recorded as `created_by`.
    """
    try:
        return await svc.create_diagnosis(payload, created_by=str(current_user.id))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# ── POST /{diagnosis_id}/analyse ──────────────────────────────────────────────

@router.post(
    "/{diagnosis_id}/analyse",
    response_model=DiagnosisResponse,
    status_code=status.HTTP_200_OK,
    summary="Run AI prediction and clinical recommendations",
    responses={
        400: {"description": "Invalid diagnosis ID format"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient role"},
        404: {"description": "Diagnosis record not found"},
        500: {"description": "AI prediction or recommendation engine failure"},
    },
)
async def analyse_diagnosis(
    diagnosis_id: str,
    _user: UserInDB = Depends(
        require_roles(UserRole.ADMIN, UserRole.DOCTOR)
    ),
    svc: DiagnosisService = Depends(_svc),
) -> DiagnosisResponse:
    """
    Trigger the full AI workflow for an existing diagnosis record.

    Executes the complete AI pipeline in sequence:

    ```
    symptoms → DiseasePredictor → predicted_disease + confidence_score
             → RecommendationEngine → recommended_tests
             → persisted to diagnosis record
    ```

    The diagnosis record's existing `symptoms` field is used as input —
    no additional request body is required.

    After a successful call the record will have:

    - `predicted_disease` — top disease prediction from the ML model
    - `confidence_score` — prediction probability (0.0 – 1.0)
    - `recommended_tests` — first-line investigations from the knowledge base
    - `status` — automatically advanced to `ai_reviewed`

    **Idempotent:** calling this endpoint multiple times on the same record
    will re-run prediction and overwrite the previous AI output.

    - **role required**: Admin · Doctor
    """
    try:
        diagnosis = await svc.generate_ai_diagnosis(diagnosis_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI engine error: {str(exc)}",
        )

    if diagnosis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnosis '{diagnosis_id}' not found.",
        )

    return diagnosis


# ── GET / ─────────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=List[DiagnosisResponse],
    status_code=status.HTTP_200_OK,
    summary="List diagnosis records",
    responses={
        400: {"description": "Invalid patient ID format"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient role"},
    },
)
async def list_diagnoses(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Max records to return"),
    patient_id: Optional[str] = Query(
        default=None,
        description="Filter by patient ObjectId — returns only that patient's diagnoses.",
    ),
    _user: UserInDB = Depends(
        require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.STAFF)
    ),
    svc: DiagnosisService = Depends(_svc),
) -> List[DiagnosisResponse]:
    """
    Paginated list of diagnosis records, sorted newest-first.

    - **skip**: offset for pagination (default 0)
    - **limit**: page size, 1–100 (default 20)
    - **patient_id**: optional filter — omit to list all diagnoses
    - **role required**: Admin · Doctor · Staff
    """
    try:
        return await svc.list_diagnoses(skip=skip, limit=limit, patient_id=patient_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# ── GET /{diagnosis_id} ───────────────────────────────────────────────────────

@router.get(
    "/{diagnosis_id}",
    response_model=DiagnosisResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a single diagnosis record by ID",
    responses={
        400: {"description": "Invalid diagnosis ID format"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient role"},
        404: {"description": "Diagnosis record not found"},
    },
)
async def get_diagnosis(
    diagnosis_id: str,
    _user: UserInDB = Depends(
        require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.STAFF)
    ),
    svc: DiagnosisService = Depends(_svc),
) -> DiagnosisResponse:
    """
    Fetch one diagnosis record by its MongoDB ObjectId.

    - **role required**: Admin · Doctor · Staff
    """
    try:
        diagnosis = await svc.get_diagnosis_by_id(diagnosis_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    if diagnosis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnosis '{diagnosis_id}' not found.",
        )

    return diagnosis


# ── PATCH /{diagnosis_id} ─────────────────────────────────────────────────────

@router.patch(
    "/{diagnosis_id}",
    response_model=DiagnosisResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a diagnosis record",
    responses={
        400: {"description": "Invalid diagnosis ID format"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient role"},
        404: {"description": "Diagnosis record not found"},
        422: {"description": "Validation error"},
    },
)
async def update_diagnosis(
    diagnosis_id: str,
    payload: DiagnosisUpdate,
    _user: UserInDB = Depends(
        require_roles(UserRole.ADMIN, UserRole.DOCTOR)
    ),
    svc: DiagnosisService = Depends(_svc),
) -> DiagnosisResponse:
    """
    Apply a partial update to an existing diagnosis record.

    Only the fields you supply are written — unspecified fields are
    left exactly as they are (true PATCH semantics).

    **Usage patterns:**

    - **AI prediction service** → update `predicted_disease` and/or
      `confidence_score`. Status advances to `ai_reviewed` automatically.
    - **Doctor review** → update `doctor_final_diagnosis`, `doctor_notes`,
      and/or `recommended_tests`. Status advances to `doctor_reviewed`
      automatically.

    **Status is managed automatically by the service:**

    `pending` → `ai_reviewed` → `doctor_reviewed`

    Clients should never send `status` manually — it is derived from
    which fields are present in the request body.

    - **role required**: Admin · Doctor
    """
    try:
        diagnosis = await svc.update_diagnosis(diagnosis_id, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    if diagnosis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnosis '{diagnosis_id}' not found.",
        )

    return diagnosis