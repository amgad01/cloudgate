import asyncio
import time
from collections.abc import Callable
from enum import Enum
from typing import Any

import structlog
from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = structlog.get_logger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        half_open_max_calls: int = 3,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def is_closed(self) -> bool:
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        return self._state == CircuitState.OPEN

    @property
    def is_half_open(self) -> bool:
        return self._state == CircuitState.HALF_OPEN

    async def _should_attempt_reset(self) -> bool:
        if self._last_failure_time is None:
            return False

        time_since_failure = time.time() - self._last_failure_time
        return time_since_failure >= self.recovery_timeout

    async def can_execute(self) -> bool:
        async with self._lock:
            if self._state == CircuitState.CLOSED:
                return True

            if self._state == CircuitState.OPEN:
                if await self._should_attempt_reset():
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    logger.info(
                        "Circuit breaker transitioning to half-open",
                        name=self.name,
                    )
                    return True
                return False

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls < self.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False

            return False

    async def record_success(self) -> None:
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.half_open_max_calls:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    logger.info(
                        "Circuit breaker closed after recovery",
                        name=self.name,
                    )
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0

    async def record_failure(self) -> None:
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._success_count = 0
                logger.warning(
                    "Circuit breaker opened after half-open failure",
                    name=self.name,
                )
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    self._state = CircuitState.OPEN
                    logger.warning(
                        "Circuit breaker opened after failures",
                        name=self.name,
                        failure_count=self._failure_count,
                    )

    async def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        if not await self.can_execute():
            raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is open")

        try:
            result = await func(*args, **kwargs)
            await self.record_success()
            return result
        except Exception:
            await self.record_failure()
            raise

    def get_stats(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": self._last_failure_time,
        }


class CircuitBreakerOpenError(Exception):
    pass


class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: Any,
        circuit_breaker: CircuitBreaker,
        exclude_paths: list[str] | None = None,
    ):
        super().__init__(app)
        self.circuit_breaker = circuit_breaker
        self.exclude_paths = exclude_paths or ["/health", "/metrics"]

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Check if circuit allows execution
        if not await self.circuit_breaker.can_execute():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "Service temporarily unavailable",
                    "circuit_breaker": self.circuit_breaker.name,
                    "state": self.circuit_breaker.state.value,
                    "retry_after": self.circuit_breaker.recovery_timeout,
                },
                headers={
                    "Retry-After": str(self.circuit_breaker.recovery_timeout),
                },
            )

        try:
            response = await call_next(request)

            # Record success for successful responses
            if response.status_code < 500:
                await self.circuit_breaker.record_success()
            else:
                await self.circuit_breaker.record_failure()

            return response

        except Exception:
            await self.circuit_breaker.record_failure()
            raise


class CircuitBreakerRegistry:
    def __init__(self) -> None:
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()

    async def get_or_create(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
    ) -> CircuitBreaker:
        async with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(
                    name=name,
                    failure_threshold=failure_threshold,
                    recovery_timeout=recovery_timeout,
                )
            return self._breakers[name]

    def get(self, name: str) -> CircuitBreaker | None:
        return self._breakers.get(name)

    def get_all_stats(self) -> list[dict[str, Any]]:
        return [cb.get_stats() for cb in self._breakers.values()]


# Global registry
circuit_breaker_registry = CircuitBreakerRegistry()
