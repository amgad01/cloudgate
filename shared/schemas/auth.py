import re
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import ConfigDict, EmailStr, Field, field_validator

from shared.schemas.base import BaseSchema


class UserCreate(BaseSchema):
    email: EmailStr = Field(..., description="User email address")
    password: Annotated[str, Field(min_length=8, max_length=128)] = Field(
        ..., description="User password"
    )
    first_name: Annotated[str, Field(min_length=1, max_length=50)] = Field(
        ..., description="User first name"
    )
    last_name: Annotated[str, Field(min_length=1, max_length=50)] = Field(
        ..., description="User last name"
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "first_name": "John",
                "last_name": "Doe",
            }
        }
    }


class UserLogin(BaseSchema):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
            }
        },
    )


class TokenPayload(BaseSchema):
    sub: str = Field(..., description="Subject (user ID)")
    email: str = Field(..., description="User email")
    exp: datetime = Field(..., description="Expiration time")
    iat: datetime = Field(..., description="Issued at time")
    type: str = Field(..., description="Token type (access/refresh)")
    jti: str | None = Field(None, description="JWT ID for token revocation")


class TokenResponse(BaseSchema):
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
            }
        }
    }


class RefreshTokenRequest(BaseSchema):
    refresh_token: str = Field(..., description="Refresh token")


class UserResponse(BaseSchema):
    id: UUID = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email")
    first_name: str = Field(..., description="User first name")
    last_name: str = Field(..., description="User last name")
    is_active: bool = Field(..., description="User active status")
    is_verified: bool = Field(..., description="Email verification status")
    created_at: datetime = Field(..., description="Account creation time")
    updated_at: datetime | None = Field(None, description="Last update time")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "is_active": True,
                "is_verified": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }
    }


class PasswordResetRequest(BaseSchema):
    email: EmailStr = Field(..., description="User email address")


class PasswordResetConfirm(BaseSchema):
    token: str = Field(..., description="Password reset token")
    new_password: Annotated[str, Field(min_length=8, max_length=128)] = Field(
        ..., description="New password"
    )

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class ChangePasswordRequest(BaseSchema):
    current_password: str = Field(..., description="Current password")
    new_password: Annotated[str, Field(min_length=8, max_length=128)] = Field(
        ..., description="New password"
    )

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v
