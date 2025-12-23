from typing import List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# ============================================================================
# CONSTANTS
# ============================================================================

# Valid media types
VALID_MEDIA_TYPES = {"image", "video", "audio", "document"}


# ============================================================================
# SCHEMAS
# ============================================================================


class SendTextMessageRequest(BaseModel):
    """Schema for sending a text message"""

    workspace_id: UUID
    channel_id: UUID
    to: str = Field(..., description="Recipient phone number")
    text: str = Field(..., min_length=1, description="Message text")


class SendTemplateMessageRequest(BaseModel):
    """Schema for sending a template message"""

    workspace_id: UUID
    channel_id: UUID
    to: str = Field(..., description="Recipient phone number")
    template_name: str
    template_language: str = "en"
    components: Optional[Union[dict, List[dict]]] = None


class SendMediaMessageRequest(BaseModel):
    """Schema for sending a media message"""

    workspace_id: UUID
    channel_id: UUID
    to: str = Field(..., description="Recipient phone number")
    media_type: str = Field(..., description="Type: image, video, audio, document")
    media_id: UUID = Field(..., description="Media file ID from /api/media")
    caption: Optional[str] = Field(
        None, max_length=3000, description="Optional caption"
    )

    @field_validator("media_type")
    @classmethod
    def validate_media_type(cls, v: str) -> str:
        v = v.lower()
        if v not in VALID_MEDIA_TYPES:
            raise ValueError(
                f"Invalid media_type. Must be one of: {', '.join(VALID_MEDIA_TYPES)}"
            )
        return v


class MessageResponse(BaseModel):
    """Schema for message response"""

    id: UUID
    workspace_id: UUID
    channel_id: UUID
    wa_message_id: Optional[str]
    direction: str
    from_number: str
    to_number: str
    type: str
    status: str

    class Config:
        from_attributes = True


class MessageStatusResponse(BaseModel):
    """Schema for message status response"""

    id: UUID
    wa_message_id: Optional[str]
    status: str
    delivered_at: Optional[str]
    read_at: Optional[str]


class MessageQueuedResponse(BaseModel):
    """Response for queued message"""

    id: UUID
    workspace_id: UUID
    channel_id: UUID
    to_number: str
    type: str
    status: str
    media_id: Optional[UUID] = None
    queued: bool = True


__all__ = [
    "SendTextMessageRequest",
    "SendTemplateMessageRequest",
    "SendMediaMessageRequest",
    "MessageResponse",
    "MessageStatusResponse",
    "MessageQueuedResponse",
]
