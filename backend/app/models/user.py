from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import string

from bson import ObjectId
from pydantic import BaseModel, EmailStr, Field, field_validator


# ──────────────────────────────────────────────────────────────
# User Roles
# ──────────────────────────────────────────────────────────────

class UserRole(str, Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    STAFF = "staff"


# ──────────────────────────────────────────────────────────────
# MongoDB ObjectId Helper
# ──────────────────────────────────────────────────────────────

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value, info=None):
        if isinstance(value, ObjectId):
            return str(value)

        if not ObjectId.is_valid(value):
            raise ValueError("Invalid ObjectId")

        return str(value)

# ──────────────────────────────────────────────────────────────
# MongoDB User Document
# ──────────────────────────────────────────────────────────────

class UserInDB(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    full_name: str
    email: EmailStr
    hashed_password: str

    role: UserRole = UserRole.STAFF
    is_active: bool = True

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }


# ──────────────────────────────────────────────────────────────
# Register Request
# ──────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    # Only admin should assign roles later.
    role: UserRole = UserRole.STAFF

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str):

        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter.")

        if not any(c.islower() for c in password):
            raise ValueError("Password must contain at least one lowercase letter.")

        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one digit.")

        if not any(c in string.punctuation for c in password):
            raise ValueError("Password must contain at least one special character.")

        return password


# ──────────────────────────────────────────────────────────────
# Login Request
# ──────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ──────────────────────────────────────────────────────────────
# Safe User Response
# ──────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None


# ──────────────────────────────────────────────────────────────
# JWT Token Response
# ──────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


# ──────────────────────────────────────────────────────────────
# Generic API Response
# ──────────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    success: bool
    message: str