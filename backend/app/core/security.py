from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings


# ─────────────────────────────────────────────────────────────
# Password Hashing
# ─────────────────────────────────────────────────────────────

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.bcrypt_rounds,
)


def hash_password(password: str) -> str:
    """Generate bcrypt hash."""
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    print("Entered password:", password)
    print("Entered length:", len(password))

    print("Hash:", hashed_password)
    print("Hash length:", len(hashed_password))

    return pwd_context.verify(password, hashed_password)


# ─────────────────────────────────────────────────────────────
# JWT Token Helpers
# ─────────────────────────────────────────────────────────────

def create_access_token(
    user_id: str,
    role: str,
    extra_data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create JWT access token.
    """

    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    payload = {
        "sub": user_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
    }

    if extra_data:
        payload.update(extra_data)

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate JWT access token.
    """

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        if payload.get("type") != "access":
            raise JWTError("Invalid token type.")

        return payload

    except JWTError:
        raise


# ─────────────────────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────────────────────

def token_expires_in_seconds() -> int:
    """Return access token lifetime."""
    return settings.access_token_expire_minutes * 60