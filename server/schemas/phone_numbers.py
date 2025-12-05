"""
Pydantic schemas for Phone Number API.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# ERROR SCHEMAS
# ============================================================================


class ErrorDetail(BaseModel):
    """Structured error detail."""

    code: str = Field(..., description="Error code (e.g., 'INVALID_TOKEN')")
    message: str = Field(..., description="Human-readable error message")


class ErrorResponse(BaseModel):
    """Standard error response wrapper."""

    detail: ErrorDetail


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class PhoneNumberCreate(BaseModel):
    """Request schema for registering a new phone number."""

    workspace_id: UUID = Field(..., description="Workspace UUID")
    phone_number_id: str = Field(
        ..., description="Meta's Phone Number ID from Business Suite"
    )
    access_token: str = Field(
        ..., description="System User Access Token with whatsapp_business_messaging permission"
    )
    display_name: Optional[str] = Field(None, description="Friendly name")
    business_id: Optional[str] = Field(
        None, description="WhatsApp Business Account ID (WABA ID)"
    )


class PhoneNumberUpdate(BaseModel):
    """Request schema for updating phone number settings."""

    display_name: Optional[str] = Field(None, description="Friendly name")
    access_token: Optional[str] = Field(
        None, description="Will be validated if provided"
    )
    status: Optional[str] = Field(
        None, description="Status: pending, active, or disabled"
    )


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class PhoneNumberResponse(BaseModel):
    """Response schema for full phone number details."""

    id: UUID
    workspace_id: UUID
    phone_number: str
    phone_number_id: str
    display_name: Optional[str] = None
    business_id: Optional[str] = None
    quality_rating: str = Field(
        default="UNKNOWN", description="GREEN/YELLOW/RED/UNKNOWN"
    )
    message_limit: int = 1000
    tier: Optional[str] = None
    status: str = "pending"
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PhoneNumberListResponse(BaseModel):
    """Paginated list of phone numbers."""

    data: List[PhoneNumberResponse]
    total: int
    limit: int
    offset: int


class PhoneNumberSyncResponse(BaseModel):
    """Response for sync operation."""

    id: UUID
    synced_at: datetime
    phone_number: str
    quality_rating: str
    message_limit: int
    tier: Optional[str] = None
    status: str
