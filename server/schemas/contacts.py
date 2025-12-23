"""
Pydantic schemas for Contact Management API.
"""

import re
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# ============================================================================
# CONSTANTS
# ============================================================================

# E.164 phone number regex - allows 1-15 total digits including country code
E164_REGEX = re.compile(r"^\+[1-9]\d{0,14}$")


# ============================================================================
# SCHEMAS
# ============================================================================


class ContactCreate(BaseModel):
    """Schema for creating a new contact (identity only)"""

    workspace_id: UUID
    phone_number: str = Field(
        ..., description="Phone number in E.164 format (e.g., +15551234567)"
    )
    name: Optional[str] = Field(None, max_length=255)
    source_channel_id: Optional[UUID] = Field(
        None, description="Channel that acquired this contact (for attribution)"
    )
    tags: Optional[List[str]] = Field(
        default_factory=list, description="Labels/tags for the contact"
    )

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        v = v.strip()
        if not E164_REGEX.match(v):
            raise ValueError(
                "Phone number must be in E.164 format (e.g., +15551234567)"
            )
        return v


class ContactUpdate(BaseModel):
    """Schema for updating a contact (identity fields only)"""

    name: Optional[str] = Field(None, max_length=255)
    tags: Optional[List[str]] = None


class ContactResponse(BaseModel):
    """Schema for contact response (workspace-level identity)"""

    id: UUID
    workspace_id: UUID
    wa_id: str
    phone_number: str
    name: Optional[str]
    source_channel_id: Optional[UUID]
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContactListResponse(BaseModel):
    """Schema for paginated contact list"""

    data: List[ContactResponse]
    total: int
    limit: int
    offset: int


class ImportRowResult(BaseModel):
    """Result for a single import row"""

    row_number: int
    phone_number: Optional[str]
    status: str  # "imported", "updated", "failed"
    reason: Optional[str] = None


class ImportResponse(BaseModel):
    """Schema for import response"""

    total_rows: int
    imported: int
    updated: int
    failed: int
    results: List[ImportRowResult]


__all__ = [
    "ContactCreate",
    "ContactUpdate",
    "ContactResponse",
    "ContactListResponse",
    "ImportRowResult",
    "ImportResponse",
    "E164_REGEX",
]
