from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.auth.models.user import User
from services.profile.api.dependencies import (
    get_current_user,
    get_db,
    validate_service_token,
)
from services.profile.models.profile import UserPreferences, UserProfile
from shared.database.redis import get_redis
from shared.schemas.profile import (
    FullProfileResponse,
    PreferencesResponse,
    ProfileResponse,
    UpdatePreferencesRequest,
    UpdateProfileRequest,
)

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


async def _invalidate_cache(user_id: UUID) -> None:
    redis = get_redis()
    await redis.delete(f"profile:{user_id}")
    await redis.delete(f"preferences:{user_id}")


@router.get(
    "/{user_id}",
    response_model=FullProfileResponse,
    summary="Get profile + preferences",
    description="Fetch profile and preferences for a user. No auth required to read in this sample.",
)
async def get_profile(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> FullProfileResponse:
    profile = await db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
    prefs = await db.scalar(
        select(UserPreferences).where(UserPreferences.user_id == user_id)
    )
    return FullProfileResponse(
        profile=ProfileResponse.model_validate(profile) if profile else None,
        preferences=PreferencesResponse.model_validate(prefs) if prefs else None,
    )


@router.put(
    "/{user_id}",
    response_model=ProfileResponse,
    summary="Update profile (self)",
    description=(
        "Update profile fields for the authenticated user.\n\n"
        "Headers: Authorization: Bearer <access_token>\n"
        "Body: any subset of bio, avatar_url, location, website, github_url, linkedin_url"
    ),
)
async def update_profile(
    user_id: UUID,
    payload: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfileResponse:
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot update another user"
        )

    profile = await db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
    if profile is None:
        profile = UserProfile(user_id=user_id)
        db.add(profile)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    await db.flush()
    await _invalidate_cache(user_id)
    return ProfileResponse.model_validate(profile)


@router.put(
    "/{user_id}/preferences",
    response_model=PreferencesResponse,
    summary="Update preferences (self)",
    description=(
        "Update preferences for the authenticated user.\n\n"
        "Headers: Authorization: Bearer <access_token>\n"
        "Body: any subset of theme, language, timezone, email_notifications, privacy_level, two_factor_enabled"
    ),
)
async def update_preferences(
    user_id: UUID,
    payload: UpdatePreferencesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PreferencesResponse:
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot update another user"
        )

    prefs = await db.scalar(
        select(UserPreferences).where(UserPreferences.user_id == user_id)
    )
    if prefs is None:
        prefs = UserPreferences(user_id=user_id)
        db.add(prefs)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(prefs, field, value)

    await db.flush()
    await _invalidate_cache(user_id)
    return PreferencesResponse.model_validate(prefs)


@router.get(
    "/service/{user_id}",
    summary="Internal fetch (service-to-service)",
    description=(
        "Internal endpoint for other services.\n\n"
        "Headers: X-Service-Auth: <SECRET_KEY>"
    ),
)
async def get_profile_for_service(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _service_auth: str = Depends(validate_service_token),
) -> dict[str, dict[str, Any] | None]:
    profile = await db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
    prefs = await db.scalar(
        select(UserPreferences).where(UserPreferences.user_id == user_id)
    )
    return {
        "profile": (
            ProfileResponse.model_validate(profile).model_dump() if profile else None
        ),
        "preferences": (
            PreferencesResponse.model_validate(prefs).model_dump() if prefs else None
        ),
    }


@router.get(
    "/health",
    summary="Health check",
    description="Basic liveness endpoint",
)
async def health() -> dict[str, str]:
    return {"status": "healthy"}
