# Shared Pydantic schemas
from shared.schemas.auth import TokenPayload, TokenResponse, UserCreate, UserLogin
from shared.schemas.base import BaseSchema, ErrorResponse, PaginatedResponse
from shared.schemas.profile import (
    FullProfileResponse,
    PreferencesResponse,
    ProfileResponse,
    UpdatePreferencesRequest,
    UpdateProfileRequest,
)

__all__ = [
    "BaseSchema",
    "PaginatedResponse",
    "ErrorResponse",
    "TokenPayload",
    "TokenResponse",
    "UserCreate",
    "UserLogin",
    "UpdateProfileRequest",
    "UpdatePreferencesRequest",
    "ProfileResponse",
    "PreferencesResponse",
    "FullProfileResponse",
]
