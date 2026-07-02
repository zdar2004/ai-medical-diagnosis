import re
from datetime import date, datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

# Reuse PyObjectId defined in user.py — single source of truth
from app.models.user import PyObjectId


# ── Enums ─────────────────────────────────────────────────────────────────────

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class BloodGroup(str, Enum):
    A_POS  = "A+"
    A_NEG  = "A-"
    B_POS  = "B+"
    B_NEG  = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"
    O_POS  = "O+"
    O_NEG  = "O-"
    UNKNOWN = "unknown"


# ── Module-level helpers ───────────────────────────────────────────────────────

# Accepted phone formats:
#   +923001234567        international, no separator
#   +92-300-1234567      international, hyphen-separated
#   03001234567          local Pakistani format
_PHONE_RE = re.compile(
    r"^\+?[\d]{1,3}[-\s]?[\d]{3,5}[-\s]?[\d]{4,7}$"
)


def calculate_age(date_of_birth: date) -> int:
    """
    Return age in whole years as of today.
    Called by the service layer when building PatientResponse — never stored.

    Examples
    --------
    >>> calculate_age(date(1995, 4, 20))   # run on 2025-06-27 → 30
    30
    """
    today = date.today()
    return (
        today.year
        - date_of_birth.year
        - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
    )


def _validate_phone(value: str, field_label: str = "Phone") -> str:
    """
    Strip whitespace, then assert the value matches _PHONE_RE.
    Raises ValueError with a clear message on failure.
    Shared by PatientCreate, PatientUpdate, and EmergencyContact.
    """
    value = value.strip()
    if not value:
        raise ValueError(f"{field_label} number cannot be blank.")
    if not _PHONE_RE.match(value):
        raise ValueError(
            f"{field_label} '{value}' is not a recognised format. "
            "Accepted: +923001234567 · +92-300-1234567 · 03001234567"
        )
    return value



# ── Sub-document: Emergency Contact ───────────────────────────────────────────

class EmergencyContact(BaseModel):
    """Embedded document — stored inside the patient document."""

    name: str = Field(..., min_length=2, max_length=100, examples=["Ahmed Dar"])
    relationship: str = Field(..., min_length=2, max_length=50, examples=["Father"])
    phone: str = Field(..., min_length=7, max_length=20, examples=["+92-300-1234567"])

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return _validate_phone(v, "Emergency contact phone")


# ── Sub-document: Previous Diagnosis entry ────────────────────────────────────

class DiagnosisEntry(BaseModel):
    """A single past diagnosis record embedded in the patient document."""

    condition: str = Field(..., min_length=2, max_length=200, examples=["Type 2 Diabetes"])
    diagnosed_on: Optional[date] = Field(default=None, examples=["2022-06-15"])
    notes: Optional[str] = Field(default=None, max_length=1000)


# ── Internal DB document (never sent to client raw) ───────────────────────────

class PatientInDB(BaseModel):
    """Mirrors the exact shape stored in the MongoDB 'patients' collection."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    # ── Identity ──────────────────────────────────────────────────────────────
    first_name: str
    last_name: str
    gender: Gender
    date_of_birth: date          # age is derived via calculate_age(), never stored

    # ── Contact ───────────────────────────────────────────────────────────────
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None

    # ── Medical ───────────────────────────────────────────────────────────────
    blood_group: BloodGroup = BloodGroup.UNKNOWN
    emergency_contact: Optional[EmergencyContact] = None
    allergies: List[str] = Field(default_factory=list)
    medications: List[str] = Field(default_factory=list)
    previous_diagnoses: List[DiagnosisEntry] = Field(default_factory=list)
    medical_history: Optional[str] = None

    # ── Meta ──────────────────────────────────────────────────────────────────
    created_by: Optional[str] = None   # user _id who registered the patient
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}


# ── Request schema: Create ────────────────────────────────────────────────────

class PatientCreate(BaseModel):
    """Inbound payload for registering a new patient."""

    # ── Identity ──────────────────────────────────────────────────────────────
    first_name: str = Field(..., min_length=1, max_length=100, examples=["Zaina"])
    last_name: str = Field(..., min_length=1, max_length=100, examples=["Dar"])
    gender: Gender = Field(..., examples=["female"])
    date_of_birth: date = Field(..., examples=["1995-04-20"])

    # ── Contact ───────────────────────────────────────────────────────────────
    phone: str = Field(..., min_length=7, max_length=20, examples=["+92-300-9876543"])
    email: Optional[EmailStr] = Field(default=None, examples=["zaina@example.com"])
    address: Optional[str] = Field(default=None, max_length=500, examples=["House 12, Street 4, Lahore"])

    # ── Medical ───────────────────────────────────────────────────────────────
    blood_group: BloodGroup = Field(default=BloodGroup.UNKNOWN, examples=["B+"])
    emergency_contact: Optional[EmergencyContact] = None
    allergies: List[str] = Field(default_factory=list, examples=[["Penicillin", "Dust"]])
    medications: List[str] = Field(default_factory=list, examples=[["Metformin 500mg"]])
    previous_diagnoses: List[DiagnosisEntry] = Field(default_factory=list)
    medical_history: Optional[str] = Field(default=None, max_length=5000)

    # ── Validators ────────────────────────────────────────────────────────────

    @field_validator("first_name", "last_name")
    @classmethod
    def normalise_name(cls, v: str) -> str:
        """Strip edges, collapse inner whitespace, apply title case.
        " muhammad  akram " → "Muhammad Akram"
        """
        return " ".join(v.split()).title()

    @field_validator("date_of_birth")
    @classmethod
    def dob_not_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Date of birth cannot be in the future.")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return _validate_phone(v, "Phone")

    @field_validator("email", mode="before")
    @classmethod
    def normalise_email(cls, v: Optional[str]) -> Optional[str]:
        """Lowercase the email address before Pydantic's EmailStr check runs."""
        if isinstance(v, str):
            return v.strip().lower() or None
        return v

    @field_validator("medical_history", mode="before")
    @classmethod
    def normalise_medical_history(cls, v: Optional[str]) -> Optional[str]:
        """Trim whitespace; return None if the result is empty."""
        if isinstance(v, str):
            stripped = v.strip()
            return stripped if stripped else None
        return v

    @field_validator("allergies", "medications", mode="before")
    @classmethod
    def strip_list_items(cls, v: list) -> list:
        """Remove accidental whitespace from list entries."""
        if isinstance(v, list):
            return [item.strip() for item in v if isinstance(item, str) and item.strip()]
        return v


# ── Request schema: Update (all fields optional — PATCH semantics) ────────────

class PatientUpdate(BaseModel):
    """
    Inbound payload for partial updates.
    Every field is Optional — only supplied fields will be written.
    """

    # ── Identity ──────────────────────────────────────────────────────────────
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None

    # ── Contact ───────────────────────────────────────────────────────────────
    phone: Optional[str] = Field(default=None, min_length=7, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = Field(default=None, max_length=500)

    # ── Medical ───────────────────────────────────────────────────────────────
    blood_group: Optional[BloodGroup] = None
    emergency_contact: Optional[EmergencyContact] = None
    allergies: Optional[List[str]] = None
    medications: Optional[List[str]] = None
    previous_diagnoses: Optional[List[DiagnosisEntry]] = None
    medical_history: Optional[str] = Field(default=None, max_length=5000)

    # ── Validators ────────────────────────────────────────────────────────────

    @field_validator("first_name", "last_name")
    @classmethod
    def normalise_name(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            return " ".join(v.split()).title()
        return v

    @field_validator("date_of_birth")
    @classmethod
    def dob_not_future(cls, v: Optional[date]) -> Optional[date]:
        if v and v > date.today():
            raise ValueError("Date of birth cannot be in the future.")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return _validate_phone(v, "Phone")
        return v

    @field_validator("email", mode="before")
    @classmethod
    def normalise_email(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            return v.strip().lower() or None
        return v

    @field_validator("medical_history", mode="before")
    @classmethod
    def normalise_medical_history(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            stripped = v.strip()
            return stripped if stripped else None
        return v

    @field_validator("allergies", "medications", mode="before")
    @classmethod
    def strip_list_items(cls, v) -> Optional[list]:
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

class PatientResponse(BaseModel):
    """
    Safe patient representation returned to API consumers.
    Computes 'age' at serialisation time from date_of_birth.
    """

    id: str
    first_name: str
    last_name: str
    gender: Gender
    age: int
    date_of_birth: date
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    blood_group: BloodGroup
    emergency_contact: Optional[EmergencyContact] = None
    allergies: List[str]
    medications: List[str]
    previous_diagnoses: List[DiagnosisEntry]
    medical_history: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}