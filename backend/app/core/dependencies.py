from typing import List

from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.core.security import decode_access_token
from app.database import db_manager
from app.models.user import UserInDB, UserRole

# HTTPBearer extracts the token from "Authorization: Bearer <token>"
bearer_scheme = HTTPBearer(auto_error=True)


# ── Token → UserInDB ──────────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> UserInDB:
    """
    Decode the JWT, look up the user in MongoDB, and return them.
    Raises HTTP 401 for any auth failure.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Fetch from DB — ensures deleted / deactivated users are rejected
    doc = await db_manager.users.find_one({"_id": ObjectId(user_id)})
    if doc is None:
        raise credentials_exception

    user = UserInDB(**{**doc, "_id": str(doc["_id"])})

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact an administrator.",
        )

    return user


# ── Active-user shortcut ──────────────────────────────────────────────────────

async def get_active_user(
    current_user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    """Alias that reads more clearly on routes that just need 'any logged-in user'."""
    return current_user


# ── RBAC factory ──────────────────────────────────────────────────────────────

def require_roles(*roles: UserRole):
    """
    Dependency factory.  Use as:

        @router.get("/admin-only")
        async def view(user = Depends(require_roles(UserRole.ADMIN))):
            ...

    Accepts multiple roles for AND-logic:

        Depends(require_roles(UserRole.ADMIN, UserRole.DOCTOR))
    """
    allowed: List[UserRole] = list(roles)

    async def _check(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. Required role(s): "
                    f"{', '.join(r.value for r in allowed)}."
                ),
            )
        return current_user

    return _check