import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from shared.config import AuthConfig
from shared.database.redis import RedisManager
from shared.schemas.auth import TokenPayload, TokenResponse


class TokenService:
    def __init__(self, config: AuthConfig, redis: RedisManager) -> None:
        self.config = config
        self.redis = redis
        self._blacklist_prefix = "token:blacklist:"

    def _build_jwt_token(
        self,
        subject: str,
        email: str,
        token_type: str,
        expires_delta: timedelta,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        now = datetime.now(UTC)
        expire = now + expires_delta

        payload = {
            "sub": subject,
            "email": email,
            "type": token_type,
            "iat": now,
            "exp": expire,
            "jti": str(uuid.uuid4()),
        }

        if extra_claims:
            payload.update(extra_claims)

        return str(
            jwt.encode(
                payload,
                self.config.jwt_secret_key,
                algorithm=self.config.jwt_algorithm,
            )
        )

    def create_access_token(
        self,
        subject: str,
        email: str,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        expires_delta = timedelta(minutes=self.config.access_token_expire_minutes)
        return self._build_jwt_token(
            subject=subject,
            email=email,
            token_type="access",
            expires_delta=expires_delta,
            extra_claims=extra_claims,
        )

    def create_refresh_token(
        self,
        subject: str,
        email: str,
    ) -> str:
        expires_delta = timedelta(days=self.config.refresh_token_expire_days)
        return self._build_jwt_token(
            subject=subject,
            email=email,
            token_type="refresh",
            expires_delta=expires_delta,
        )

    def create_token_pair(
        self,
        subject: str,
        email: str,
        extra_claims: dict[str, Any] | None = None,
    ) -> TokenResponse:
        access_token = self.create_access_token(
            subject=subject,
            email=email,
            extra_claims=extra_claims,
        )
        refresh_token = self.create_refresh_token(
            subject=subject,
            email=email,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.config.access_token_expire_minutes * 60,
        )

    def decode_token(self, token: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm],
            )
            return dict(payload)
        except JWTError as e:
            raise ValueError(f"Invalid token: {e}") from e

    async def verify_access_token(self, token: str) -> TokenPayload:
        payload = self.decode_token(token)

        if payload.get("type") != "access":
            raise ValueError("Invalid token type")

        jti = payload.get("jti")
        if jti and await self._is_blacklisted(jti):
            raise ValueError("Token has been revoked")

        return TokenPayload(
            sub=payload["sub"],
            email=payload["email"],
            exp=datetime.fromtimestamp(payload["exp"], tz=UTC),
            iat=datetime.fromtimestamp(payload["iat"], tz=UTC),
            type=payload["type"],
            jti=jti,
        )

    async def verify_refresh_token(self, token: str) -> TokenPayload:
        payload = self.decode_token(token)

        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")

        jti = payload.get("jti")
        if jti and await self._is_blacklisted(jti):
            raise ValueError("Token has been revoked")

        return TokenPayload(
            sub=payload["sub"],
            email=payload["email"],
            exp=datetime.fromtimestamp(payload["exp"], tz=UTC),
            iat=datetime.fromtimestamp(payload["iat"], tz=UTC),
            type=payload["type"],
            jti=jti,
        )

    async def _is_blacklisted(self, jti: str) -> bool:
        key = f"{self._blacklist_prefix}{jti}"
        return await self.redis.exists(key)

    async def blacklist_token(self, token: str) -> None:
        try:
            payload = self.decode_token(token)
            jti = payload.get("jti")
            if jti:
                exp = payload.get("exp", 0)
                ttl = max(0, exp - int(datetime.now(UTC).timestamp()))
                key = f"{self._blacklist_prefix}{jti}"
                await self.redis.set(key, "1", expire=ttl)
        except Exception:
            pass  # Token already invalid

    async def blacklist_user_tokens(self, user_id: str) -> None:
        key = f"user:logout:{user_id}"
        await self.redis.set(
            key,
            str(int(datetime.now(UTC).timestamp())),
            expire=self.config.refresh_token_expire_days * 24 * 60 * 60,
        )
