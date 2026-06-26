from typing import List

from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import get_current_user, require_roles
from app.database import get_database
from app.models.user import UserInDB, UserResponse, UserRole
from app.services.auth_service import AuthService

router = APIRouter()


def _svc(db: AsyncIOMotorDatabase = Depends(get_database)) -> AuthService:
    return AuthService(db)


# ── GET /me ───────────────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the currently authenticated user",
)
async def get_me(
    current_user: UserInDB = Depends(get_current_user),
) -> UserResponse:
    """
    Returns the profile of the user whose token was supplied.
    Any authenticated user (admin / doctor / staff) can call this.
    """
    return UserResponse(
    id=str(current_user.id),
    full_name=current_user.full_name,
    email=current_user.email,
    role=current_user.role,
    is_active=current_user.is_active,
    created_at=current_user.created_at,
    last_login=current_user.last_login,
)


# ── GET / (admin only) ────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=List[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="List all users — Admin only",
    responses={
        403: {"description": "Insufficient role"},
    },
)
async def list_users(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Max records to return"),
    _admin: UserInDB = Depends(require_roles(UserRole.ADMIN)),
    svc: AuthService = Depends(_svc),
) -> List[UserResponse]:
    """
    Paginated list of every registered user.
    **Requires Admin role.**
    """
    return await svc.list_users(skip=skip, limit=limit)


# ── GET /role-check — demo endpoint for every role ────────────────────────────

@router.get(
    "/role-check/doctor",
    response_model=dict,
    summary="Doctor + Admin access demo",
)
async def doctor_area(
    user: UserInDB = Depends(require_roles(UserRole.DOCTOR, UserRole.ADMIN)),
):
    """Accessible by Doctors and Admins. Returns a confirmation message."""
    return {"message": f"Welcome Dr. {user.full_name}. Access granted.", "role": user.role}


@router.get(
    "/role-check/staff",
    response_model=dict,
    summary="All roles access demo",
)
async def staff_area(
    user: UserInDB = Depends(require_roles(UserRole.STAFF, UserRole.DOCTOR, UserRole.ADMIN)),
):
    """Accessible by any authenticated user regardless of role."""
    return {"message": f"Hello {user.full_name}. Staff area confirmed.", "role": user.role}