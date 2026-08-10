from fastapi import APIRouter, Depends, status
from app.api.dependencies.auth import get_current_active_user
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.models.user import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter()


def _svc(db: AsyncIOMotorDatabase = Depends(get_database)) -> AuthService:
    """Inject AuthService with the live DB handle."""
    return AuthService(db)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    responses={
        409: {"description": "Email already registered"},
        422: {"description": "Validation error"},
    },
)
async def register(
    payload: RegisterRequest,
    svc: AuthService = Depends(_svc),
) -> UserResponse:
    return await svc.register(payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login and receive a JWT access token",
    responses={
        401: {"description": "Incorrect email or password"},
        403: {"description": "Account deactivated"},
    },
)
async def login(
    payload: LoginRequest,
    svc: AuthService = Depends(_svc),
) -> TokenResponse:
    return await svc.login(payload)

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current logged-in user",
)
async def get_me(
    current_user=Depends(get_current_active_user),
):
    return UserResponse(
        id=str(current_user["_id"]),
        full_name=current_user["full_name"],
        email=current_user["email"],
        role=current_user["role"],
        is_active=current_user["is_active"],
        created_at=current_user["created_at"],
        last_login=current_user.get("last_login"),
    )