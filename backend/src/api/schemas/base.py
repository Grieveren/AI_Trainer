"""Pydantic V2 base schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base Pydantic schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        use_enum_values=True,
    )


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""

    created_at: datetime = Field(
        ..., description="Timestamp when the record was created"
    )
    updated_at: datetime = Field(
        ..., description="Timestamp when the record was last updated"
    )


class IDSchema(BaseSchema):
    """Schema with ID field."""

    id: int = Field(..., description="Unique identifier", gt=0)


class BaseResponseSchema(IDSchema, TimestampSchema):
    """Base response schema with ID and timestamps."""

    pass


class PaginationParams(BaseSchema):
    """Pagination parameters for list endpoints."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(
        default=20, ge=1, le=100, description="Number of items per page"
    )


class PaginatedResponse(BaseSchema):
    """Paginated response wrapper."""

    items: list = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items", ge=0)
    page: int = Field(..., description="Current page number", ge=1)
    page_size: int = Field(..., description="Number of items per page", ge=1)
    pages: int = Field(..., description="Total number of pages", ge=0)


class ErrorResponse(BaseSchema):
    """Error response schema."""

    detail: str = Field(..., description="Error message")
    type: Optional[str] = Field(None, description="Error type for client handling")


class SuccessResponse(BaseSchema):
    """Generic success response."""

    message: str = Field(..., description="Success message")
    data: Optional[dict] = Field(None, description="Optional response data")


class HealthCheckResponse(BaseSchema):
    """Health check response schema."""

    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="API version")
    database: str = Field(..., description="Database status")
    redis: str = Field(..., description="Redis status")
