"""
Pydantic schemas for WhatsApp Channels (formerly Phone Number API).
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


class ChannelCreate(BaseModel):
    """Request schema for registering a new channel."""

    workspace_id: Optional[UUID] = Field(
        None, description="Workspace UUID (optional if in path)"
    )
    meta_phone_number_id: str = Field(
        ..., description="Meta's Phone Number ID from Business Suite"
    )
    access_token: str = Field(
        ...,
        description="System User Access Token with whatsapp_business_messaging permission",
    )
    display_name: Optional[str] = Field(None, description="Friendly name")
    meta_business_id: Optional[str] = Field(
        None, description="WhatsApp Business Account ID (WABA ID)"
    )


class ChannelUpdate(BaseModel):
    """Request schema for updating channel settings."""

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


class ChannelResponse(BaseModel):
    """Response schema for full channel details."""

    id: UUID
    workspace_id: UUID
    phone_number: str
    meta_phone_number_id: str
    display_name: Optional[str] = None
    meta_business_id: Optional[str] = None
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


class ChannelListResponse(BaseModel):
    """Paginated list of channels."""

    data: List[ChannelResponse]
    total: int
    limit: int
    offset: int


class ChannelSyncResponse(BaseModel):
    """Response for sync operation."""

    id: UUID
    synced_at: datetime
    phone_number: str
    quality_rating: str
    message_limit: int
    tier: Optional[str] = None
    status: str


__all__ = [
    "ErrorDetail",
    "ErrorResponse",
    "ChannelCreate",
    "ChannelUpdate",
    "ChannelResponse",
    "ChannelListResponse",
    "ChannelSyncResponse",
]
