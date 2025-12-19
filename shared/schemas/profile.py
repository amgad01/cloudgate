from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class UpdateProfileRequest(BaseModel):
    bio: str | None = Field(None, max_length=500)
    avatar_url: HttpUrl | None = None
    location: str | None = Field(None, max_length=100)
    website: HttpUrl | None = None
    github_url: HttpUrl | None = None
    linkedin_url: HttpUrl | None = None


class UpdatePreferencesRequest(BaseModel):
    theme: str | None = Field(None, pattern=r"^(light|dark|auto)$")
    language: str | None = Field(None, pattern=r"^[a-z]{2}$")
    timezone: str | None = None
    email_notifications: bool | None = None
    privacy_level: str | None = Field(None, pattern=r"^(public|friends|private)$")
    two_factor_enabled: bool | None = None


class ProfileResponse(BaseModel):
    user_id: UUID
    bio: str | None
    avatar_url: str | None
    location: str | None
    website: str | None
    github_url: str | None
    linkedin_url: str | None
    created_at: datetime | None
    updated_at: datetime | None

    class Config:
        from_attributes = True


class PreferencesResponse(BaseModel):
    user_id: UUID
    theme: str
    language: str
    timezone: str
    email_notifications: bool
    privacy_level: str
    two_factor_enabled: bool
    created_at: datetime | None
    updated_at: datetime | None

    class Config:
        from_attributes = True


class FullProfileResponse(BaseModel):
    profile: ProfileResponse | None
    preferences: PreferencesResponse | None
