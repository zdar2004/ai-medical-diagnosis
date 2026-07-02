from datetime import datetime
from enum import Enum
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Role enum ─────────────────────────────────────────────────────────────────

class UserRole(str, Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    STAFF = "staff"


# ── ObjectId helper ───────────────────────────────────────────────────────────

class PyObjectId(str):
    """
    Serialises MongoDB ObjectId to/from a plain string.
    Implemented with the Pydantic v2 native hook to avoid the v1-compat
    deprecation warning produced by __get_validators__.
    """

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema

        return core_schema.no_info_plain_validator_function(
            cls.validate,
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError(f"Invalid ObjectId: {v}")
        return str(v)


# ── Internal DB document (never sent to client) ───────────────────────────────

class UserInDB(BaseModel):
    """Mirrors the exact shape stored in MongoDB."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    full_name: str
    email: str
    hashed_password: str
    role: UserRole = UserRole.STAFF
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}


# ── Request schemas (inbound) ─────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, examples=["Dr. Sarah Khan"])
    email: EmailStr = Field(..., examples=["sarah@medisys.ai"])
    password: str = Field(..., min_length=8, max_length=128, examples=["StrongPass123!"])
    role: UserRole = Field(default=UserRole.STAFF, examples=["doctor"])

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., examples=["sarah@medisys.ai"])
    password: str = Field(..., examples=["StrongPass123!"])


# ── Response schemas (outbound) ───────────────────────────────────────────────

class UserResponse(BaseModel):
    """Safe user representation — no password hash."""

    id: str
    full_name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int          # seconds
    user: UserResponse


class MessageResponse(BaseModel):
    """Generic success/error envelope."""

    success: bool
    message: str