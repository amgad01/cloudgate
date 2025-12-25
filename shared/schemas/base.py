from datetime import datetime
from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        json_schema_extra={"example": {}},
    )


class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime | None = None


T = TypeVar("T")


class PaginatedResponse[T](BaseSchema):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class ErrorResponse(BaseSchema):
    error: str
    detail: str | dict[str, Any] | list[Any] | None = None
    code: str | None = None
    timestamp: datetime | None = None

    def __init__(self, **data: Any) -> None:
        if "timestamp" not in data:
            data["timestamp"] = datetime.utcnow()
        super().__init__(**data)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Not Found",
                "detail": "Resource not found",
                "code": "RESOURCE_NOT_FOUND",
                "timestamp": "2024-01-01T00:00:00Z",
            }
        }
    )


class HealthResponse(BaseSchema):
    status: str
    service: str
    version: str
    timestamp: datetime
    dependencies: dict[str, dict[str, Any]] | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "service": "auth",
                "version": "1.0.0",
                "timestamp": "2024-01-01T00:00:00Z",
                "dependencies": {
                    "database": {"status": "healthy"},
                    "redis": {"status": "healthy"},
                },
            }
        }
    )


class MessageResponse(BaseSchema):
    message: str
    success: bool = True

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Operation completed successfully",
                "success": True,
            }
        }
    )
