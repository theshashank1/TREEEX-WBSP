"""
Pydantic schemas for Template Management API.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TemplateCreate(BaseModel):
    """Schema for creating a new template"""

    workspace_id: UUID
    phone_number_id: UUID
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Template name (lowercase, no spaces)",
    )
    category: str = Field(
        ..., description="Template category: MARKETING, UTILITY, or AUTHENTICATION"
    )
    language: str = Field(
        default="en", description="Language code (e.g., 'en', 'es', 'fr')"
    )
    components: dict = Field(
        ..., description="Template components (header, body, footer, buttons)"
    )


class TemplateUpdate(BaseModel):
    """Schema for updating template"""

    components: Optional[dict] = None
    status: Optional[str] = None


class TemplateResponse(BaseModel):
    """Schema for template response"""

    id: UUID
    workspace_id: UUID
    phone_number_id: UUID
    name: str
    category: str
    language: str
    status: str
    meta_template_id: Optional[str]
    components: dict
    rejection_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    """Schema for paginated template list"""

    data: list[TemplateResponse]
    total: int
    limit: int
    offset: int


__all__ = [
    "TemplateCreate",
    "TemplateUpdate",
    "TemplateResponse",
    "TemplateListResponse",
]
