import logging
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.security import (
    create_access_token,
    hash_password,
    token_expires_in_seconds,
    verify_password,
)
from app.models.user import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserInDB,
    UserResponse,
)

logger = logging.getLogger(__name__)


def _doc_to_user_response(doc: dict) -> UserResponse:
    """Convert MongoDB document to public user response."""
    return UserResponse(
        id=str(doc["_id"]),
        full_name=doc["full_name"],
        email=doc["email"],
        role=doc["role"],
        is_active=doc["is_active"],
        created_at=doc["created_at"],
        last_login=doc.get("last_login"),
    )


class AuthService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.users = db["users"]

    async def create_indexes(self):
        """Create required indexes."""
        await self.users.create_index("email", unique=True)

    # ------------------------------------------------------------------
    # Register
    # ------------------------------------------------------------------

    async def register(self, payload: RegisterRequest) -> UserResponse:
        email = payload.email.lower().strip()

        existing = await self.users.find_one({"email": email})

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )

        now = datetime.now(timezone.utc)

        doc = {
            "full_name": payload.full_name.strip(),
            "email": email,
            "hashed_password": hash_password(payload.password),
            "role": payload.role.value,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
            "last_login": None,
        }

        result = await self.users.insert_one(doc)

        doc["_id"] = result.inserted_id

        logger.info("User registered: %s (%s)", email, payload.role.value)

        return _doc_to_user_response(doc)

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    async def login(self, payload: LoginRequest) -> TokenResponse:
        email = payload.email.lower().strip()

        invalid_credentials = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

        doc = await self.users.find_one({"email": email})

        if doc is None:
            raise invalid_credentials

        if not verify_password(payload.password, doc["hashed_password"]):
            raise invalid_credentials

        if not doc.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated.",
            )

        # Update last login
        last_login = datetime.now(timezone.utc)

        await self.users.update_one(
            {"_id": doc["_id"]},
            {
                "$set": {
                    "last_login": last_login,
                    "updated_at": last_login,
                }
            },
        )

        doc["last_login"] = last_login
        doc["updated_at"] = last_login

        token = create_access_token(
            user_id=str(doc["_id"]),
            role=doc["role"],
        )

        logger.info("User logged in: %s (%s)", email, doc["role"])

        return TokenResponse(
            access_token=token,
            expires_in=token_expires_in_seconds(),
            user=_doc_to_user_response(doc),
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def get_by_id(self, user_id: str) -> Optional[dict]:
        if not ObjectId.is_valid(user_id):
            return None

        return await self.users.find_one(
            {"_id": ObjectId(user_id)}
        )

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 50,
    ):
        cursor = (
            self.users.find({}, {"hashed_password": 0})
            .skip(skip)
            .limit(limit)
        )

        docs = await cursor.to_list(length=limit)

        return [_doc_to_user_response(doc) for doc in docs]