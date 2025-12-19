from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from datetime import datetime
from typing import Any

from shared.schemas.base import HealthResponse


def _determine_overall_status(dependencies: Mapping[str, Any]) -> str:
    statuses = [dep.get("status") for dep in dependencies.values() if isinstance(dep, dict)]
    return "healthy" if all(status == "healthy" for status in statuses) else "degraded"


DependencyCheck = Callable[[], Awaitable[Any]]


async def gather_dependency_health(
    checks: Mapping[str, DependencyCheck],
) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for name, check in checks.items():
        results[name] = await check()
    return results


def build_health_response(
    service: str,
    dependencies: Mapping[str, Any],
    version: str = "1.0.0",
) -> HealthResponse:
    return HealthResponse(
        status=_determine_overall_status(dependencies),
        service=service,
        version=version,
        timestamp=datetime.utcnow(),
        dependencies=dict(dependencies),
    )
