from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from services.auth.api.dependencies import get_current_user, get_db_session
from services.auth.models.user import User
from services.auth.services.auth_service import AuthService
from shared.api.helpers import build_health_response, gather_dependency_health
from shared.config import get_auth_config
from shared.database.connection import get_database
from shared.database.redis import get_redis
from shared.schemas.auth import (
    ChangePasswordRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from shared.schemas.base import ErrorResponse, HealthResponse, MessageResponse

router = APIRouter(tags=["Authentication"])


def get_auth_service(session: AsyncSession = Depends(get_db_session)) -> AuthService:
    config = get_auth_config()
    redis = get_redis()
    return AuthService(session=session, redis=redis, config=config)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check the health status of the auth service",
)
async def health_check() -> HealthResponse:
    db = get_database()
    redis = get_redis()

    dependencies = await gather_dependency_health(
        {
            "database": db.health_check,
            "redis": redis.health_check,
        }
    )

    return build_health_response(service="auth", dependencies=dependencies)


@router.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register User",
    description="Register a new user account with email and password",
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Validation error", "model": ErrorResponse},
        409: {"description": "Email already registered", "model": ErrorResponse},
    },
)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    user = await auth_service.register(user_data)
    return UserResponse.model_validate(user)


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="Login",
    description="Authenticate user and get access and refresh tokens",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials", "model": ErrorResponse},
    },
)
async def login(
    credentials: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    tokens = await auth_service.login(credentials)
    return tokens


@router.post(
    "/auth/refresh",
    response_model=TokenResponse,
    summary="Refresh Token",
    description="Get a new access token using a refresh token",
    responses={
        200: {"description": "Token refreshed successfully"},
        401: {"description": "Invalid refresh token", "model": ErrorResponse},
    },
)
async def refresh_token(
    token_request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    tokens = await auth_service.refresh_token(token_request.refresh_token)
    return tokens


@router.post(
    "/auth/logout",
    response_model=MessageResponse,
    summary="Logout",
    description="Logout user and invalidate tokens",
    responses={
        200: {"description": "Logout successful"},
        401: {"description": "Unauthorized", "model": ErrorResponse},
    },
)
async def logout(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    await auth_service.logout(str(current_user.id))
    return MessageResponse(message="Successfully logged out")


@router.get(
    "/auth/me",
    response_model=UserResponse,
    summary="Get Current User",
    description="Get current authenticated user profile",
    responses={
        200: {"description": "User profile retrieved"},
        401: {"description": "Unauthorized", "model": ErrorResponse},
    },
)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post(
    "/auth/change-password",
    response_model=MessageResponse,
    summary="Change Password",
    description="Change current user's password",
    responses={
        200: {"description": "Password changed successfully"},
        400: {"description": "Invalid current password", "model": ErrorResponse},
        401: {"description": "Unauthorized", "model": ErrorResponse},
    },
)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    await auth_service.change_password(
        user=current_user,
        current_password=password_data.current_password,
        new_password=password_data.new_password,
    )
    return MessageResponse(message="Password changed successfully")


@router.post(
    "/auth/verify-token",
    response_model=UserResponse,
    summary="Verify Token",
    description="Verify access token validity and return user info",
    responses={
        200: {"description": "Token is valid"},
        401: {"description": "Invalid token", "model": ErrorResponse},
    },
)
async def verify_token(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
