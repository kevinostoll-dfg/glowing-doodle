"""Common Pydantic schemas."""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    status_code: int


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str = "0.1.0"
    database: str = "unknown"
    redis: str = "unknown"
