from typing import Any

import httpx
import structlog
from fastapi import HTTPException, Request, status
from fastapi.responses import Response
from tenacity import retry, stop_after_attempt, wait_exponential

from shared.config import GatewayConfig
from shared.middleware.circuit_breaker import CircuitBreaker, circuit_breaker_registry

logger = structlog.get_logger(__name__)


class ProxyService:
    def __init__(self, config: GatewayConfig) -> None:
        self.config = config
        self._client: httpx.AsyncClient | None = None

        # Service URL mapping
        self.service_urls = {
            "auth": config.auth_service_url,
            "profile": config.profile_service_url,
        }

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    self.config.request_timeout,
                    connect=self.config.request_connect_timeout,
                    read=self.config.request_read_timeout,
                ),
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def _resolve_service_url(self, service: str) -> str:
        url = self.service_urls.get(service)
        if not url:
            raise ValueError(f"Unknown service: {service}")
        return url

    async def _get_or_create_circuit_breaker(self, service: str) -> CircuitBreaker:
        return await circuit_breaker_registry.get_or_create(
            name=f"proxy_{service}",
            failure_threshold=self.config.circuit_breaker_failure_threshold,
            recovery_timeout=self.config.circuit_breaker_recovery_timeout,
        )

    def _get_forwarded_headers(self, request: Request) -> dict[str, str]:
        headers_to_forward = [
            "authorization",
            "content-type",
            "accept",
            "x-request-id",
            "x-correlation-id",
            "user-agent",
        ]

        headers = {}
        for header in headers_to_forward:
            value = request.headers.get(header)
            if value:
                headers[header] = value

        # Add gateway identifier
        headers["x-forwarded-by"] = "cloudgate-gateway"

        return headers

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _make_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        content: bytes | None = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        return await self.client.request(
            method=method,
            url=url,
            headers=headers,
            content=content,
            params=params,
        )

    async def proxy_request(
        self,
        service: str,
        path: str,
        method: str,
        request: Request,
    ) -> Response:
        try:
            base_url = self._resolve_service_url(service)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(e),
            ) from e

        # Get circuit breaker
        circuit_breaker = await self._get_or_create_circuit_breaker(service)

        # Check circuit breaker
        if not await circuit_breaker.can_execute():
            logger.warning(
                "Circuit breaker open for service",
                service=service,
                state=circuit_breaker.state.value,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service {service} is temporarily unavailable",
                headers={"Retry-After": str(circuit_breaker.recovery_timeout)},
            )

        # Build request
        url = f"{base_url}{path}"
        headers = self._get_forwarded_headers(request)

        # Get request body
        content = None
        if method in ["POST", "PUT", "PATCH"]:
            content = await request.body()

        # Get query params
        params = dict(request.query_params)

        try:
            # Make request
            logger.info(
                "Proxying request",
                service=service,
                method=method,
                path=path,
            )

            response = await self._make_request(
                method=method,
                url=url,
                headers=headers,
                content=content,
                params=params,
            )

            # Record success
            if response.status_code < 500:
                await circuit_breaker.record_success()
            else:
                await circuit_breaker.record_failure()

            # Return response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type"),
            )

        except httpx.ConnectError as e:
            await circuit_breaker.record_failure()
            logger.error(
                "Connection error to service",
                service=service,
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to connect to {service} service",
            ) from e

        except httpx.TimeoutException as e:
            await circuit_breaker.record_failure()
            logger.error(
                "Timeout connecting to service",
                service=service,
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Timeout connecting to {service} service",
            ) from e

        except Exception as e:
            await circuit_breaker.record_failure()
            logger.error(
                "Error proxying request",
                service=service,
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Error communicating with downstream service",
            ) from e

    async def health_check_services(self) -> dict[str, dict[str, Any]]:
        results: dict[str, dict[str, Any]] = {}

        for service, base_url in self.service_urls.items():
            try:
                response = await self.client.get(
                    f"{base_url}/api/v1/health",
                    timeout=5.0,
                )
                if response.status_code == 200:
                    results[service] = {"status": "healthy"}
                else:
                    results[service] = {
                        "status": "unhealthy",
                        "code": response.status_code,
                    }
            except Exception as e:
                results[service] = {
                    "status": "unhealthy",
                    "error": str(e),
                }

        return results
