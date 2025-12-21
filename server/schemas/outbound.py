"""
Outbound Message Schemas - server/schemas/outbound.py

Pydantic models for validating outbound WhatsApp messages payload.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator

# =============================================================================
# BUTTON/ROW MODELS
# =============================================================================


class Button(BaseModel):
    """Interactive button definition."""

    id: str = Field(..., max_length=256, description="Unique button ID")
    title: str = Field(..., max_length=20, description="Button text")


class ListRow(BaseModel):
    """Row in an interactive list section."""

    id: str = Field(..., max_length=200, description="Unique row ID")
    title: str = Field(..., max_length=24, description="Row title")
    description: Optional[str] = Field(
        None, max_length=72, description="Row description"
    )


class ListSection(BaseModel):
    """Section in an interactive list."""

    title: Optional[str] = Field(None, max_length=24, description="Section title")
    rows: List[ListRow] = Field(..., min_length=1, max_length=10)


# =============================================================================
# TEMPLATE COMPONENTS
# =============================================================================


class TemplateParameter(BaseModel):
    """Parameter for template component."""

    type: Literal["text", "currency", "date_time", "image", "video", "document"]
    text: Optional[str] = None
    currency: Optional[Dict[str, Any]] = None
    date_time: Optional[Dict[str, Any]] = None
    image: Optional[Dict[str, str]] = None  # {"link": "..."} or {"id": "..."}
    video: Optional[Dict[str, str]] = None
    document: Optional[Dict[str, str]] = None


class TemplateComponent(BaseModel):
    """Template component (header, body, button)."""

    type: Literal["header", "body", "button"]
    sub_type: Optional[Literal["quick_reply", "url"]] = None
    index: Optional[int] = None  # For buttons
    parameters: List[TemplateParameter] = Field(default_factory=list)


# =============================================================================
# BASE MESSAGE
# =============================================================================


class BaseOutboundMessage(BaseModel):
    """Base schema for outbound messages."""

    type: str = Field(..., description="Message type identifier")
    message_id: str = Field(..., description="UUID - idempotency key")
    workspace_id: str = Field(..., description="Workspace UUID")
    phone_number_id: str = Field(..., description="Meta phone_number_id")
    to_number: str = Field(..., description="Recipient E.164 phone number")

    # Optional fields
    reply_to_message_id: Optional[str] = Field(
        None, description="wa_message_id to reply to"
    )
    sent_by: Optional[str] = Field(
        None, description="workspace_member UUID who triggered send"
    )
    conversation_id: Optional[str] = Field(
        None, description="Conversation UUID for tracking"
    )

    @field_validator("to_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """Ensure phone number is in E.164 format and numeric."""
        cleaned = v.lstrip("+")
        if not cleaned.isdigit():
            raise ValueError("Phone number must contain only digits")
        if len(cleaned) < 10 or len(cleaned) > 15:
            raise ValueError("Phone number must be 10-15 digits")
        return v


# =============================================================================
# MESSAGE TYPE SCHEMAS
# =============================================================================


class TextMessage(BaseOutboundMessage):
    """Text message payload."""

    type: Literal["text_message"] = "text_message"
    text: str = Field(..., max_length=4096, description="Message text")
    preview_url: bool = Field(False, description="Show URL previews")


class TemplateMessage(BaseOutboundMessage):
    """Template message payload."""

    type: Literal["template_message"] = "template_message"
    template_name: str = Field(..., description="Approved template name")
    language_code: str = Field("en", description="Template language code")
    components: Optional[List[TemplateComponent]] = Field(
        None, description="Template variable components"
    )


class MediaMessage(BaseOutboundMessage):
    """Media message (image, video, audio, document, sticker)."""

    type: Literal["media_message"] = "media_message"
    media_type: Literal["image", "video", "audio", "document", "sticker"]
    media_url: Optional[str] = Field(None, description="Public HTTPS URL of media")
    media_id: Optional[str] = Field(None, description="Meta media ID from upload")
    caption: Optional[str] = Field(None, max_length=1024, description="Media caption")
    filename: Optional[str] = Field(None, description="Filename for documents")

    @field_validator("media_url", "media_id")
    @classmethod
    def validate_media_source(cls, v, info):
        """At least one media source must be provided."""
        return v

    def model_post_init(self, __context):
        """Validate key presence."""
        if not self.media_url and not self.media_id:
            raise ValueError("Either media_url or media_id must be provided")


class InteractiveButtonsMessage(BaseOutboundMessage):
    """Interactive message with reply buttons."""

    type: Literal["interactive_buttons"] = "interactive_buttons"
    body_text: str = Field(..., max_length=1024, description="Main message body")
    buttons: List[Button] = Field(
        ..., min_length=1, max_length=3, description="Reply buttons"
    )
    header_text: Optional[str] = Field(
        None, max_length=60, description="Optional header"
    )
    footer_text: Optional[str] = Field(
        None, max_length=60, description="Optional footer"
    )


class InteractiveListMessage(BaseOutboundMessage):
    """Interactive list message."""

    type: Literal["interactive_list"] = "interactive_list"
    body_text: str = Field(..., max_length=1024, description="Main message body")
    button_text: str = Field(..., max_length=20, description="List button text")
    sections: List[ListSection] = Field(..., min_length=1, max_length=10)
    header_text: Optional[str] = Field(
        None, max_length=60, description="Optional header"
    )
    footer_text: Optional[str] = Field(
        None, max_length=60, description="Optional footer"
    )


class LocationMessage(BaseOutboundMessage):
    """Location pin message."""

    type: Literal["location_message"] = "location_message"
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    name: Optional[str] = Field(None, description="Location name")
    address: Optional[str] = Field(None, description="Location address")


class ReactionMessage(BaseOutboundMessage):
    """Reaction emoji message."""

    type: Literal["reaction_message"] = "reaction_message"
    target_message_id: str = Field(..., description="wa_message_id to react to")
    emoji: str = Field(..., description="Emoji character")


class MarkAsReadMessage(BaseOutboundMessage):
    """Mark message as read."""

    type: Literal["mark_as_read"] = "mark_as_read"
    target_message_id: str = Field(..., description="wa_message_id to mark as read")
    to_number: Optional[str] = None  # type: ignore


# =============================================================================
# UNION TYPE FOR PARSING
# =============================================================================

OutboundMessage = Union[
    TextMessage,
    TemplateMessage,
    MediaMessage,
    InteractiveButtonsMessage,
    InteractiveListMessage,
    LocationMessage,
    ReactionMessage,
    MarkAsReadMessage,
]


def parse_outbound_message(data: Dict[str, Any]) -> OutboundMessage:
    """
    Parse a dict into the appropriate outbound message type.

    Raises ValueError if type unknown.
    """
    message_type = data.get("type")

    type_map = {
        "text_message": TextMessage,
        "template_message": TemplateMessage,
        "media_message": MediaMessage,
        "interactive_buttons": InteractiveButtonsMessage,
        "interactive_list": InteractiveListMessage,
        "location_message": LocationMessage,
        "reaction_message": ReactionMessage,
        "mark_as_read": MarkAsReadMessage,
    }

    model_class = type_map.get(message_type)
    if not model_class:
        raise ValueError(f"Unknown message type: {message_type}")

    return model_class.model_validate(data)
