import asyncio
import logging
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.auth.models.user import User
from services.auth.services.password_service import hash_password, verify_password
from services.auth.services.token_service import TokenService
from shared.config import AuthConfig
from shared.database.redis import RedisManager
from shared.schemas.auth import TokenResponse, UserCreate, UserLogin


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
        # Conservative default timeout for DB-bound operations (seconds)
        self._db_timeout_s: float = 3.0

    async def register(self, user_data: UserCreate) -> User:
        try:
            existing = await asyncio.wait_for(
                self.session.execute(
                    select(User).where(User.email == user_data.email.lower())
                ),
                timeout=self._db_timeout_s,
            )
        except TimeoutError as e:
            self._logger.warning(
                "register.query_timeout email=%s timeout_s=%.2f", user_data.email, self._db_timeout_s
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service temporarily unavailable. Please try again.",
            ) from e
        except Exception as e:  # database/driver errors
            self._logger.exception("register.query_error email=%s", user_data.email)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to process registration at this time.",
            ) from e
        if existing.scalar_one_or_none():
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

        try:
            self.session.add(user)
            await asyncio.wait_for(self.session.commit(), timeout=self._db_timeout_s)
            await asyncio.wait_for(self.session.refresh(user), timeout=self._db_timeout_s)
        except TimeoutError as e:
            self._logger.warning("register.commit_timeout user_id=%s", getattr(user, "id", None))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service temporarily unavailable. Please try again.",
            ) from e
        except Exception as e:
            self._logger.exception("register.commit_error email=%s", user_data.email)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to process registration at this time.",
            ) from e

        return user

    async def login(self, credentials: UserLogin) -> TokenResponse:
        try:
            result = await asyncio.wait_for(
                self.session.execute(
                    select(User).where(User.email == credentials.email.lower())
                ),
                timeout=self._db_timeout_s,
            )
        except TimeoutError:
            # Intentionally do not reveal system details to user
            self._logger.warning(
                "login.query_timeout email=%s timeout_s=%.2f", credentials.email, self._db_timeout_s
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service temporarily unavailable. Please try again.",
            )
        except Exception:
            self._logger.exception("login.query_error email=%s", credentials.email)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service temporarily unavailable. Please try again.",
            )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled",
            )

        user.last_login = datetime.now(UTC)
        try:
            await asyncio.wait_for(self.session.commit(), timeout=self._db_timeout_s)
        except TimeoutError:
            self._logger.warning("login.commit_timeout user_id=%s", getattr(user, "id", None))
            # Do not fail login if updating last_login times out
        except Exception:
            self._logger.exception("login.commit_error user_id=%s", getattr(user, "id", None))

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
        try:
            result = await asyncio.wait_for(
                self.session.execute(select(User).where(User.id == payload.sub)),
                timeout=self._db_timeout_s,
            )
        except TimeoutError:
            self._logger.warning("refresh.query_timeout user_id=%s", payload.sub)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service temporarily unavailable. Please try again.",
            )
        except Exception:
            self._logger.exception("refresh.query_error user_id=%s", payload.sub)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service temporarily unavailable. Please try again.",
            )
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

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
        try:
            await asyncio.wait_for(self.session.commit(), timeout=self._db_timeout_s)
        except TimeoutError:
            self._logger.warning("change_password.commit_timeout user_id=%s", getattr(user, "id", None))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service temporarily unavailable. Please try again.",
            )
        except Exception:
            self._logger.exception("change_password.commit_error user_id=%s", getattr(user, "id", None))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to change password at this time.",
            )

        # Invalidate all existing tokens
        await self.token_service.blacklist_user_tokens(str(user.id))

    async def get_user_by_id(self, user_id: str) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()
