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
    preview_url: bool = Field(False, description="Show URL previews")
    reply_to_message_id: Optional[str] = Field(
        None, description="wa_message_id to reply to"
    )


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


# ============================================================================
# NEW MESSAGE TYPE SCHEMAS
# ============================================================================


class SendLocationRequest(BaseModel):
    """Schema for sending a location message"""

    workspace_id: UUID
    channel_id: UUID
    to: str = Field(..., description="Recipient phone number")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    name: Optional[str] = Field(None, max_length=100, description="Location name")
    address: Optional[str] = Field(None, max_length=200, description="Location address")


class ButtonItem(BaseModel):
    """Single button for interactive message"""

    id: str = Field(..., max_length=256)
    title: str = Field(..., max_length=20)


class SendInteractiveButtonsRequest(BaseModel):
    """Schema for sending interactive buttons message"""

    workspace_id: UUID
    channel_id: UUID
    to: str = Field(..., description="Recipient phone number")
    body_text: str = Field(..., max_length=1024, description="Message body")
    buttons: List[ButtonItem] = Field(..., min_length=1, max_length=3)
    header_text: Optional[str] = Field(None, max_length=60)
    footer_text: Optional[str] = Field(None, max_length=60)


class ListRowItem(BaseModel):
    """Row in an interactive list section"""

    id: str = Field(..., max_length=200)
    title: str = Field(..., max_length=24)
    description: Optional[str] = Field(None, max_length=72)


class ListSectionItem(BaseModel):
    """Section in an interactive list"""

    title: Optional[str] = Field(None, max_length=24)
    rows: List[ListRowItem] = Field(..., min_length=1, max_length=10)


class SendInteractiveListRequest(BaseModel):
    """Schema for sending interactive list message"""

    workspace_id: UUID
    channel_id: UUID
    to: str = Field(..., description="Recipient phone number")
    body_text: str = Field(..., max_length=1024, description="Message body")
    button_text: str = Field(..., max_length=20, description="List button text")
    sections: List[ListSectionItem] = Field(..., min_length=1, max_length=10)
    header_text: Optional[str] = Field(None, max_length=60)
    footer_text: Optional[str] = Field(None, max_length=60)


class SendReactionRequest(BaseModel):
    """Schema for sending a reaction to a message"""

    workspace_id: UUID
    channel_id: UUID
    to: str = Field(..., description="Recipient phone number")
    message_id: str = Field(..., description="wa_message_id to react to")
    emoji: str = Field(..., description="Emoji character")


__all__ = [
    "SendTextMessageRequest",
    "SendTemplateMessageRequest",
    "SendMediaMessageRequest",
    "SendLocationRequest",
    "SendInteractiveButtonsRequest",
    "SendInteractiveListRequest",
    "SendReactionRequest",
    "ButtonItem",
    "ListRowItem",
    "ListSectionItem",
    "MessageResponse",
    "MessageStatusResponse",
    "MessageQueuedResponse",
]
