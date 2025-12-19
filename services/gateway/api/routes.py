from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response

from services.gateway.services.proxy_service import ProxyService
from shared.api.helpers import build_health_response, gather_dependency_health
from shared.config import get_gateway_config
from shared.database.redis import get_redis
from shared.middleware.circuit_breaker import circuit_breaker_registry
from shared.schemas.base import HealthResponse

router = APIRouter()


def get_proxy_service(request: Request) -> ProxyService:
    return request.app.state.proxy_service  # type: ignore


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check the health status of the API Gateway",
)
async def health_check(
    proxy_service: ProxyService = Depends(get_proxy_service),
) -> HealthResponse:
    redis = get_redis()

    dependency_checks = await gather_dependency_health(
        {"redis": redis.health_check}
    )
    services_health = await proxy_service.health_check_services()

    dependencies = {
        **dependency_checks,
        **services_health,
    }

    return build_health_response(service="gateway", dependencies=dependencies)


async def _proxy_request(
    request: Request,
    proxy_service: ProxyService,
    service: str,
    path: str,
    method: str,
) -> Response:
    return await proxy_service.proxy_request(
        service=service,
        path=path,
        method=method,
        request=request,
    )


@router.get(
    "/circuit-breakers",
    summary="Circuit Breaker Status",
    description="Get status of all circuit breakers",
)
async def circuit_breaker_status() -> dict[str, Any]:
    return {"circuit_breakers": circuit_breaker_registry.get_all_stats()}


@router.get(
    "/api/config",
    summary="Frontend Configuration",
    description="Get runtime configuration for frontend (API base URL, environment)",
)
async def get_frontend_config() -> dict[str, str | None]:
    config = get_gateway_config()
    return {
        "apiBaseUrl": config.frontend_api_url,
        "environment": config.app_env,
    }


# ===== Auth Service Proxy Routes =====


@router.post(
    "/auth/register",
    summary="Register User",
    description="Proxy to auth service - Register a new user",
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Validation error"},
        409: {"description": "Email already registered"},
    },
)
async def proxy_register(
    request: Request,
    proxy_service: ProxyService = Depends(get_proxy_service),
) -> Response:
    return await _proxy_request(
        request,
        proxy_service,
        service="auth",
        path="/api/v1/auth/register",
        method="POST",
    )


@router.post(
    "/auth/login",
    summary="Login",
    description="Proxy to auth service - User login",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
    },
)
async def proxy_login(
    request: Request,
    proxy_service: ProxyService = Depends(get_proxy_service),
) -> Response:
    return await _proxy_request(
        request,
        proxy_service,
        service="auth",
        path="/api/v1/auth/login",
        method="POST",
    )


@router.post(
    "/auth/refresh",
    summary="Refresh Token",
    description="Proxy to auth service - Refresh access token",
    responses={
        200: {"description": "Token refreshed"},
        401: {"description": "Invalid refresh token"},
    },
)
async def proxy_refresh(
    request: Request,
    proxy_service: ProxyService = Depends(get_proxy_service),
) -> Response:
    return await _proxy_request(
        request,
        proxy_service,
        service="auth",
        path="/api/v1/auth/refresh",
        method="POST",
    )


@router.post(
    "/auth/logout",
    summary="Logout",
    description="Proxy to auth service - User logout",
    responses={
        200: {"description": "Logout successful"},
        401: {"description": "Unauthorized"},
    },
)
async def proxy_logout(
    request: Request,
    proxy_service: ProxyService = Depends(get_proxy_service),
) -> Response:
    return await _proxy_request(
        request,
        proxy_service,
        service="auth",
        path="/api/v1/auth/logout",
        method="POST",
    )


@router.get(
    "/auth/me",
    summary="Get Current User",
    description="Proxy to auth service - Get current user profile",
    responses={
        200: {"description": "User profile retrieved"},
        401: {"description": "Unauthorized"},
    },
)
async def proxy_get_me(
    request: Request,
    proxy_service: ProxyService = Depends(get_proxy_service),
) -> Response:
    return await _proxy_request(
        request,
        proxy_service,
        service="auth",
        path="/api/v1/auth/me",
        method="GET",
    )


# ===== Profile Service Proxy Routes =====


@router.api_route(
    "/profile/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    summary="Profile proxy",
    description="Proxy to profile service for profile/preferences endpoints",
)
async def proxy_profile(
    path: str,
    request: Request,
    proxy_service: ProxyService = Depends(get_proxy_service),
) -> Response:
    return await _proxy_request(
        request,
        proxy_service,
        service="profile",
        path=f"/api/v1/profile/{path}",
        method=request.method,
    )
