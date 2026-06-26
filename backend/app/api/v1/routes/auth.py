from fastapi import APIRouter, Depends, status
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