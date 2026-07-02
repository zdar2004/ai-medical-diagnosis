from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import require_roles
from app.database import get_database
from app.models.patient import PatientCreate, PatientResponse, PatientUpdate
from app.models.user import UserInDB, UserRole
from app.services.patient_service import PatientService

router = APIRouter(
    prefix="/patients",
    tags=["Patients"],
)


def _svc(db: AsyncIOMotorDatabase = Depends(get_database)) -> PatientService:
    """Inject PatientService with the live DB handle."""
    return PatientService(db)


# ── POST / ────────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new patient",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient role"},
        422: {"description": "Validation error"},
    },
)
async def create_patient(
    payload: PatientCreate,
    current_user: UserInDB = Depends(
        require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.STAFF)
    ),
    svc: PatientService = Depends(_svc),
) -> PatientResponse:
    """
    Register a new patient record.

    - **date_of_birth**: ISO date string, must not be in the future
    - **phone**: `+923001234567` · `+92-300-1234567` · `03001234567`
    - **blood_group**: `A+` `A-` `B+` `B-` `AB+` `AB-` `O+` `O-` `unknown`
    - **role required**: Admin · Doctor · Staff

    The authenticated user's ID is recorded as `created_by`.
    Age is never stored — it is calculated fresh on every response.
    """
    return await svc.create_patient(payload, created_by=str(current_user.id))


# ── GET / ─────────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=List[PatientResponse],
    status_code=status.HTTP_200_OK,
    summary="List all patients",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient role"},
    },
)
async def list_patients(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Max records to return"),
    _user: UserInDB = Depends(
        require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.STAFF)
    ),
    svc: PatientService = Depends(_svc),
) -> List[PatientResponse]:
    """
    Paginated list of patients, sorted newest-first.

    - **skip**: offset for pagination (default 0)
    - **limit**: page size, 1–100 (default 20)
    - **role required**: Admin · Doctor · Staff
    """
    return await svc.list_patients(skip=skip, limit=limit)


# ── GET /{patient_id} ─────────────────────────────────────────────────────────

@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a single patient by ID",
    responses={
        400: {"description": "Invalid patient ID format"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient role"},
        404: {"description": "Patient not found"},
    },
)
async def get_patient(
    patient_id: str,
    _user: UserInDB = Depends(
        require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.STAFF)
    ),
    svc: PatientService = Depends(_svc),
) -> PatientResponse:
    """
    Fetch one patient record by their MongoDB ObjectId.

    - **role required**: Admin · Doctor · Staff
    """
    try:
        patient = await svc.get_patient_by_id(patient_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient '{patient_id}' not found.",
        )

    return patient


# ── PATCH /{patient_id} ───────────────────────────────────────────────────────

@router.patch(
    "/{patient_id}",
    response_model=PatientResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update a patient record",
    responses={
        400: {"description": "Invalid patient ID format"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient role"},
        404: {"description": "Patient not found"},
        422: {"description": "Validation error"},
    },
)
async def update_patient(
    patient_id: str,
    payload: PatientUpdate,
    _user: UserInDB = Depends(
        require_roles(UserRole.ADMIN, UserRole.DOCTOR)
    ),
    svc: PatientService = Depends(_svc),
) -> PatientResponse:
    """
    Apply a partial update to an existing patient record.

    Only the fields you supply are written — unspecified fields are
    left exactly as they are (true PATCH semantics).

    - **role required**: Admin · Doctor
    """
    try:
        patient = await svc.update_patient(patient_id, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient '{patient_id}' not found.",
        )

    return patient


# ── DELETE /{patient_id} ──────────────────────────────────────────────────────

@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a patient record — Admin only",
    responses={
        400: {"description": "Invalid patient ID format"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient role"},
        404: {"description": "Patient not found"},
    },
)
async def delete_patient(
    patient_id: str,
    _admin: UserInDB = Depends(require_roles(UserRole.ADMIN)),
    svc: PatientService = Depends(_svc),
) -> dict:
    """
    Hard-delete a patient record by ID.

    **Requires Admin role.**

    This is a hard delete — the record is permanently removed from the
    database. Soft-delete support may be added in a future phase.
    """
    try:
        deleted = await svc.delete_patient(patient_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient '{patient_id}' not found.",
        )

    return {
        "success": True,
        "message": f"Patient '{patient_id}' has been permanently deleted.",
    }