from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

# Reuse PyObjectId defined in user.py — single source of truth
from app.models.user import PyObjectId


# ── Enums ─────────────────────────────────────────────────────────────────────

class DiagnosisStatus(str, Enum):
    """
    Lifecycle of a diagnosis record.

    PENDING        — submitted by staff/doctor, awaiting AI analysis.
    AI_REVIEWED    — AI prediction attached; awaiting doctor confirmation.
    DOCTOR_REVIEWED — doctor has set the final diagnosis and closed the record.
    """
    PENDING         = "pending"
    AI_REVIEWED     = "ai_reviewed"
    DOCTOR_REVIEWED = "doctor_reviewed"


# ── Internal DB document (never sent to client raw) ───────────────────────────

class DiagnosisInDB(BaseModel):
    """Mirrors the exact shape stored in the MongoDB 'diagnoses' collection."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    # ── Core ──────────────────────────────────────────────────────────────────
    patient_id: str                          # ObjectId string of the linked patient
    symptoms: List[str]

    # ── AI output (populated by the prediction service) ───────────────────────
    predicted_disease: Optional[str] = None
    confidence_score: Optional[float] = None   # 0.0 – 1.0

    # ── Doctor review (populated after AI output) ─────────────────────────────
    doctor_final_diagnosis: Optional[str] = None
    doctor_notes: Optional[str] = None
    recommended_tests: List[str] = Field(default_factory=list)

    # ── Status ────────────────────────────────────────────────────────────────
    status: DiagnosisStatus = DiagnosisStatus.PENDING

    # ── Meta ──────────────────────────────────────────────────────────────────
    created_by: str                          # user _id who created this record
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}


# ── Request schema: Create ────────────────────────────────────────────────────

class DiagnosisCreate(BaseModel):
    """
    Inbound payload for opening a new diagnosis record.

    The caller supplies the patient and their reported symptoms.
    All AI fields (predicted_disease, confidence_score) and all doctor
    review fields are absent at creation time — they are filled by
    subsequent AI prediction and doctor review steps respectively.
    """

    # ── Core ──────────────────────────────────────────────────────────────────
    patient_id: str = Field(
        ...,
        min_length=24,
        max_length=24,
        examples=["64b1f2c8e13a4d5f6a7b8c9d"],
        description="MongoDB ObjectId of the patient this diagnosis belongs to.",
    )
    symptoms: List[str] = Field(
        ...,
        min_length=1,
        examples=[["fever", "persistent cough", "shortness of breath"]],
        description="One or more symptoms reported by or observed in the patient.",
    )

    # ── Validators ────────────────────────────────────────────────────────────

    @field_validator("patient_id")
    @classmethod
    def validate_patient_id(cls, v: str) -> str:
        """Ensure patient_id is a syntactically valid 24-hex ObjectId string."""
        from bson import ObjectId  # local import — avoids circular deps at module level
        if not ObjectId.is_valid(v):
            raise ValueError(
                f"'{v}' is not a valid patient ID. Expected a 24-character hex ObjectId."
            )
        return v

    @field_validator("symptoms", mode="before")
    @classmethod
    def normalise_symptoms(cls, v: list) -> list:
        """Strip whitespace from each symptom and discard blank entries."""
        if isinstance(v, list):
            cleaned = [item.strip().lower() for item in v if isinstance(item, str) and item.strip()]
            if not cleaned:
                raise ValueError("At least one symptom must be provided.")
            return cleaned
        return v


# ── Request schema: Update (all fields optional — PATCH semantics) ────────────

class DiagnosisUpdate(BaseModel):
    """
    Inbound payload for partial updates.
    Every field is Optional — only supplied fields will be written.

    Typical usage patterns
    ----------------------
    AI service  → sets predicted_disease, confidence_score, status=ai_reviewed.
    Doctor      → sets doctor_final_diagnosis, doctor_notes, recommended_tests,
                  status=doctor_reviewed.
    """

    # ── AI output ─────────────────────────────────────────────────────────────
    predicted_disease: Optional[str] = Field(
        default=None,
        max_length=200,
        examples=["Pulmonary Tuberculosis"],
    )
    confidence_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        examples=[0.87],
        description="AI model confidence, expressed as a probability between 0.0 and 1.0.",
    )

    # ── Doctor review ─────────────────────────────────────────────────────────
    doctor_final_diagnosis: Optional[str] = Field(
        default=None,
        max_length=200,
        examples=["Pulmonary Tuberculosis"],
    )
    doctor_notes: Optional[str] = Field(
        default=None,
        max_length=5000,
        examples=["Patient started on HRZE regimen. Follow-up in 4 weeks."],
    )
    recommended_tests: Optional[List[str]] = Field(
        default=None,
        examples=[["Chest X-Ray", "Sputum Culture", "CBC"]],
    )

    # ── Status ────────────────────────────────────────────────────────────────
    status: Optional[DiagnosisStatus] = Field(
        default=None,
        examples=["doctor_reviewed"],
    )

    # ── Validators ────────────────────────────────────────────────────────────

    @field_validator("predicted_disease", "doctor_final_diagnosis", mode="before")
    @classmethod
    def normalise_text_field(cls, v: Optional[str]) -> Optional[str]:
        """Trim whitespace; return None if the result is empty."""
        if isinstance(v, str):
            stripped = v.strip()
            return stripped if stripped else None
        return v

    @field_validator("doctor_notes", mode="before")
    @classmethod
    def normalise_doctor_notes(cls, v: Optional[str]) -> Optional[str]:
        """Trim leading/trailing whitespace; return None if the result is empty."""
        if isinstance(v, str):
            stripped = v.strip()
            return stripped if stripped else None
        return v

    @field_validator("recommended_tests", mode="before")
    @classmethod
    def normalise_recommended_tests(cls, v: Optional[list]) -> Optional[list]:
        """Strip whitespace from each test name and discard blank entries."""
        if isinstance(v, list):
            return [item.strip() for item in v if isinstance(item, str) and item.strip()]
        return v

    def to_update_dict(self) -> dict:
        """
        Return only the fields that were explicitly supplied by the caller.
        Used by the service layer to build a MongoDB $set payload.
        """
        return self.model_dump(exclude_none=True, exclude_unset=True)


# ── Response schema (outbound) ────────────────────────────────────────────────

class DiagnosisResponse(BaseModel):
    """
    Public diagnosis representation returned to API consumers.

    Both AI-generated and doctor-reviewed fields are present but may be
    None depending on how far through the review lifecycle the record is.
    """

    id: str

    # ── Core ──────────────────────────────────────────────────────────────────
    patient_id: str
    symptoms: List[str]

    # ── AI output ─────────────────────────────────────────────────────────────
    predicted_disease: Optional[str] = None
    confidence_score: Optional[float] = None

    # ── Doctor review ─────────────────────────────────────────────────────────
    doctor_final_diagnosis: Optional[str] = None
    doctor_notes: Optional[str] = None
    recommended_tests: List[str]

    # ── Status ────────────────────────────────────────────────────────────────
    status: DiagnosisStatus

    # ── Meta ──────────────────────────────────────────────────────────────────
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}