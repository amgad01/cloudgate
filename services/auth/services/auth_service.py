import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any, TypeVar

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.auth.models.user import User
from services.auth.services.password_service import hash_password, verify_password
from services.auth.services.token_service import TokenService
from shared.config import AuthConfig
from shared.database.redis import RedisManager
from shared.schemas.auth import TokenResponse, UserCreate, UserLogin

T = TypeVar("T")


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        redis: RedisManager,
        config: AuthConfig,
    ) -> None:
        self.session = session
        self.redis = redis
        self.config = config
        self.token_service = TokenService(config=config, redis=redis)
        self._logger = logging.getLogger("auth.service")
        self._db_timeout_s: float = 10.0

    async def _execute_db_operation(
        self, operation: Callable[[], Awaitable[T]], operation_name: str, **context: Any
    ) -> T:
        try:
            return await asyncio.wait_for(operation(), timeout=self._db_timeout_s)
        except TimeoutError:
            self._logger.warning(
                f"{operation_name}.timeout timeout_s={self._db_timeout_s}",
                extra=context,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service temporarily unavailable. Please try again.",
            ) from None
        except Exception:
            # Log the error with context for debugging
            self._logger.exception(f"{operation_name}.error", extra=context)
            # Re-raise the original exception to preserve error types
            raise

    def _validate_user_active(self, user: User | None, operation: str) -> User:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled",
            )

        return user

    async def register(self, user_data: UserCreate) -> User:
        # Check if user already exists
        existing_result = await self._execute_db_operation(
            lambda: self.session.execute(
                select(User).where(User.email == user_data.email.lower())
            ),
            "register.check_existing",
            email=user_data.email,
        )
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = User(
            email=user_data.email.lower(),
            hashed_password=hash_password(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            is_active=True,
            is_verified=False,  # Email verification not yet implemented
        )

        # Save user to database
        self.session.add(user)
        await self._execute_db_operation(
            lambda: self.session.commit(),
            "register.commit",
            email=user_data.email,
            user_id=getattr(user, "id", None),
        )
        await self._execute_db_operation(
            lambda: self.session.refresh(user),
            "register.refresh",
            email=user_data.email,
            user_id=user.id,
        )

        return user

    async def login(self, credentials: UserLogin) -> TokenResponse:
        # Query user by email
        result = await self._execute_db_operation(
            lambda: self.session.execute(
                select(User).where(User.email == credentials.email.lower())
            ),
            "login.query",
            email=credentials.email,
        )
        user = result.scalar_one_or_none()
        user = self._validate_user_active(user, "login")

        if not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        user.last_login = datetime.now(UTC)
        # Non-critical update - don't fail login if this times out
        try:
            await self._execute_db_operation(
                lambda: self.session.commit(),
                "login.update_last_login",
                user_id=user.id,
            )
        except Exception:
            # Log but don't fail the login for non-critical update
            self._logger.warning("login.last_login_update_failed user_id=%s", user.id)

        # Generate tokens
        tokens = self.token_service.create_token_pair(
            subject=str(user.id),
            email=user.email,
        )

        return tokens

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        try:
            payload = await self.token_service.verify_refresh_token(refresh_token)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            ) from e

        # Verify user still exists and is active
        result = await self._execute_db_operation(
            lambda: self.session.execute(select(User).where(User.id == payload.sub)),
            "refresh.query",
            user_id=payload.sub,
        )
        user = result.scalar_one_or_none()
        user = self._validate_user_active(user, "refresh_token")

        # Blacklist old refresh token
        await self.token_service.blacklist_token(refresh_token)

        # Generate new token pair
        tokens = self.token_service.create_token_pair(
            subject=str(user.id),
            email=user.email,
        )

        return tokens

    async def logout(self, user_id: str) -> None:
        await self.token_service.blacklist_user_tokens(user_id)

    async def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str,
    ) -> None:
        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        # Update password
        user.hashed_password = hash_password(new_password)
        user.updated_at = datetime.now(UTC)

        # Commit the password change
        await self._execute_db_operation(
            lambda: self.session.commit(),
            "change_password.commit",
            user_id=user.id,
        )

        # Invalidate all existing tokens
        await self.token_service.blacklist_user_tokens(str(user.id))

    async def get_user_by_id(self, user_id: str) -> User | None:
        result = await self._execute_db_operation(
            lambda: self.session.execute(select(User).where(User.id == user_id)),
            "get_user_by_id",
            user_id=user_id,
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self._execute_db_operation(
            lambda: self.session.execute(
                select(User).where(User.email == email.lower())
            ),
            "get_user_by_email",
            email=email,
        )
        return result.scalar_one_or_none()
