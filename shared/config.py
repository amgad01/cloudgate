from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "CloudGate"
    app_env: str = "development"
    debug: bool = False
    secret_key: str = "change-me-in-production"

    # JWT Settings
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Database
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/cloudgate"
    )
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_password: str | None = None

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Monitoring
    prometheus_enabled: bool = True
    prometheus_port: int = 9090

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            import json

            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
                else:
                    return [str(parsed)]
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        elif isinstance(v, list):
            return [str(item) for item in v]
        else:
            return [str(v)]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def is_development(self) -> bool:

        return self.app_env.lower() == "development"


class GatewayConfig(BaseConfig):

    service_name: str = "gateway"
    service_port: int = 8000

    # Service URLs
    auth_service_url: str = "http://localhost:8001"
    profile_service_url: str = "http://localhost:8002"

    # Frontend Configuration (injected during deployment)
    frontend_api_url: str | None = None  # Set via FRONTEND_API_URL env var

    # Circuit Breaker
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 30

    # Request Timeouts (in seconds)
    request_timeout: float = 30.0
    request_connect_timeout: float = 10.0
    request_read_timeout: float = 30.0


class AuthConfig(BaseConfig):

    service_name: str = "auth"
    service_port: int = 8001

    # Password settings
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digit: bool = True
    password_require_special: bool = True


class ProfileConfig(BaseConfig):

    service_name: str = "profile"
    service_port: int = 8002


@lru_cache
def get_gateway_config() -> GatewayConfig:
    return GatewayConfig()


@lru_cache
def get_auth_config() -> AuthConfig:
    return AuthConfig()


@lru_cache
def get_profile_config() -> ProfileConfig:
    return ProfileConfig()
