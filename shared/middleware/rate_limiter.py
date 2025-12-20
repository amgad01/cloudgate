import time
from collections.abc import Callable
from typing import Any

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from shared.database.redis import RedisManager


class RateLimiter:
    def __init__(
        self,
        redis: RedisManager,
        requests_per_window: int = 100,
        window_seconds: int = 60,
        key_prefix: str = "ratelimit",
    ) -> None:
        self.redis = redis
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.key_prefix = key_prefix

    def _build_rate_limit_key(self, identifier: str) -> str:
        return f"{self.key_prefix}:{identifier}"

    async def is_allowed(self, identifier: str) -> tuple[bool, dict[str, int]]:
        key = self._build_rate_limit_key(identifier)
        current_time = int(time.time())
        window_start = current_time - self.window_seconds

        # Use Redis sorted set for sliding window
        pipe = self.redis.client.pipeline()

        # Remove old entries outside the window
        pipe.zremrangebyscore(key, 0, window_start)

        # Count current requests in window
        pipe.zcard(key)

        # Add current request
        pipe.zadd(key, {f"{current_time}:{time.time_ns()}": current_time})

        # Set expiration to ensure bounded memory usage
        pipe.expire(key, self.window_seconds + 1)

        results = await pipe.execute()

        request_count = results[1]

        remaining = max(0, self.requests_per_window - request_count - 1)
        reset_time = current_time + self.window_seconds

        rate_limit_info = {
            "limit": self.requests_per_window,
            "remaining": remaining,
            "reset": reset_time,
            "window": self.window_seconds,
        }

        is_allowed = request_count < self.requests_per_window

        if not is_allowed:
            # Remove the request we just added since it's not allowed
            # Keep the set representative of actual processed requests
            await self.redis.client.zremrangebyscore(
                key, current_time, current_time + 1
            )
            rate_limit_info["remaining"] = 0

        return is_allowed, rate_limit_info

    async def get_current_usage(self, identifier: str) -> dict[str, int]:
        key = self._build_rate_limit_key(identifier)
        current_time = int(time.time())
        window_start = current_time - self.window_seconds

        # Clean old entries and count
        await self.redis.client.zremrangebyscore(key, 0, window_start)
        count = await self.redis.client.zcard(key)

        return {
            "limit": self.requests_per_window,
            "used": count,
            "remaining": max(0, self.requests_per_window - count),
            "reset": current_time + self.window_seconds,
        }


class RateLimitMiddleware(BaseHTTPMiddleware):

    def __init__(
        self,
        app: Any,
        rate_limiter: RateLimiter,
        identifier_func: Callable[[Request], str] | None = None,
        exclude_paths: list[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.identifier_func = identifier_func or self._default_identifier
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]

    def _default_identifier(self, request: Request) -> str:
        # Check for forwarded IP (behind proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return "unknown"

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Get identifier
        identifier = self.identifier_func(request)

        # Check rate limit
        is_allowed, rate_info = await self.rate_limiter.is_allowed(identifier)

        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": rate_info["limit"],
                    "window_seconds": rate_info["window"],
                    "retry_after": rate_info["reset"] - int(time.time()),
                },
                headers={
                    "X-RateLimit-Limit": str(rate_info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(rate_info["reset"]),
                    "Retry-After": str(rate_info["reset"] - int(time.time())),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])

        return response
