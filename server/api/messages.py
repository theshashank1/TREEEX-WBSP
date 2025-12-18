"""
Message Sending API endpoints for WhatsApp Business.
"""
import uuid as uuid_module
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.db import get_async_session
from server.core.monitoring import log_event
from server.core.redis import Queue, enqueue
from server.dependencies import User, get_current_user, get_workspace_member
from server.models.base import MessageDirection, MessageStatus
from server.models.contacts import PhoneNumber
from server.models.messaging import MediaFile, Message
from server.services import azure_storage

router = APIRouter(prefix="/messages", tags=["Messages"])

# Type aliases for dependencies
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


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
    phone_number_id: UUID
    to: str = Field(..., description="Recipient phone number")
    text: str = Field(..., min_length=1, description="Message text")


class SendTemplateMessageRequest(BaseModel):
    """Schema for sending a template message"""
    workspace_id: UUID
    phone_number_id: UUID
    to: str = Field(..., description="Recipient phone number")
    template_name: str
    template_language: str = "en"
    components: Optional[dict] = None


class SendMediaMessageRequest(BaseModel):
    """Schema for sending a media message"""
    workspace_id: UUID
    phone_number_id: UUID
    to: str = Field(..., description="Recipient phone number")
    media_type: str = Field(..., description="Type: image, video, audio, document")
    media_id: UUID = Field(..., description="Media file ID from /api/media")
    caption: Optional[str] = Field(None, max_length=3000, description="Optional caption")

    @field_validator("media_type")
    @classmethod
    def validate_media_type(cls, v: str) -> str:
        v = v.lower()
        if v not in VALID_MEDIA_TYPES:
            raise ValueError(f"Invalid media_type. Must be one of: {', '.join(VALID_MEDIA_TYPES)}")
        return v


class MessageResponse(BaseModel):
    """Schema for message response"""
    id: UUID
    workspace_id: UUID
    phone_number_id: UUID
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
    phone_number_id: UUID
    to_number: str
    type: str
    status: str
    media_id: Optional[UUID] = None
    queued: bool = True


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/send/text", response_model=MessageResponse, status_code=201)
async def send_text_message(
    data: SendTextMessageRequest,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Send a text message.
    
    NOTE: This is a PLACEHOLDER endpoint for API scaffolding.
    Actual implementation should:
    1. Find or create contact and conversation
    2. Create message record with conversation_id
    3. Queue message to Redis for async sending via WhatsApp API
    4. Return the queued message
    
    Requires workspace membership.
    """
    # Verify workspace membership
    await get_workspace_member(data.workspace_id, current_user, session)

    # Get phone number
    result = await session.execute(
        select(PhoneNumber).where(
            PhoneNumber.id == data.phone_number_id,
            PhoneNumber.deleted_at.is_(None),
        )
    )
    phone_number = result.scalar_one_or_none()

    if not phone_number:
        raise HTTPException(status_code=404, detail="Phone number not found")

    # TODO: Implement actual message sending logic
    # This would involve:
    # - Finding or creating contact
    # - Finding or creating conversation
    # - Creating message with conversation_id
    # - Queueing to Redis for sending
    
    raise HTTPException(
        status_code=501,
        detail="Message sending not yet implemented. This is a placeholder endpoint.",
    )


@router.post("/send/template", response_model=MessageResponse, status_code=201)
async def send_template_message(
    data: SendTemplateMessageRequest,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Send a template message.
    
    NOTE: This is a PLACEHOLDER endpoint for API scaffolding.
    Actual implementation should integrate with WhatsApp client,
    create conversation, and queue the message.
    
    Requires workspace membership.
    """
    # Verify workspace membership
    await get_workspace_member(data.workspace_id, current_user, session)

    # Get phone number
    result = await session.execute(
        select(PhoneNumber).where(
            PhoneNumber.id == data.phone_number_id,
            PhoneNumber.deleted_at.is_(None),
        )
    )
    phone_number = result.scalar_one_or_none()

    if not phone_number:
        raise HTTPException(status_code=404, detail="Phone number not found")

    # TODO: Implement actual template message sending
    raise HTTPException(
        status_code=501,
        detail="Template message sending not yet implemented. This is a placeholder endpoint.",
    )


@router.post("/send/media", response_model=MessageQueuedResponse, status_code=201)
async def send_media_message(
    data: SendMediaMessageRequest,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Send a media message.

    Validates the media file exists and has been uploaded,
    then queues the message for async delivery.

    Flow:
    1. Validate workspace membership
    2. Validate phone number
    3. Validate media file exists and is ready
    4. Generate SAS URL for media delivery
    5. Queue message to outbound queue

    Requires workspace membership.
    """
    # Verify workspace membership
    member = await get_workspace_member(data.workspace_id, current_user, session)

    # Get phone number
    result = await session.execute(
        select(PhoneNumber).where(
            PhoneNumber.id == data.phone_number_id,
            PhoneNumber.workspace_id == data.workspace_id,
            PhoneNumber.deleted_at.is_(None),
        )
    )
    phone_number = result.scalar_one_or_none()

    if not phone_number:
        raise HTTPException(status_code=404, detail="Phone number not found")

    # Validate media file
    result = await session.execute(
        select(MediaFile).where(
            MediaFile.id == data.media_id,
            MediaFile.workspace_id == data.workspace_id,
            MediaFile.deleted_at.is_(None),
        )
    )
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(
            status_code=404,
            detail={"code": "MEDIA_NOT_FOUND", "message": "Media file not found"},
        )

    if not media.storage_url:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "MEDIA_NOT_READY",
                "message": "Media file has not been uploaded to storage yet",
            },
        )

    # Validate media type matches
    if media.type != data.media_type:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "MEDIA_TYPE_MISMATCH",
                "message": f"Media file is of type '{media.type}', but '{data.media_type}' was specified",
            },
        )

    # Generate SAS URL for delivery (30 minute expiry for sending)
    blob_name = azure_storage.extract_blob_name_from_url(media.storage_url)
    if not blob_name:
        raise HTTPException(
            status_code=500,
            detail={"code": "STORAGE_ERROR", "message": "Failed to parse media storage URL"},
        )

    sas_url = azure_storage.generate_sas_url(blob_name, expiry_minutes=30)
    if not sas_url:
        raise HTTPException(
            status_code=500,
            detail={"code": "SAS_ERROR", "message": "Failed to generate media download URL"},
        )

    # Create a placeholder message record
    # Note: In a full implementation, this would create contact/conversation first
    message_id = uuid_module.uuid4()

    # Queue the message for async sending
    job = {
        "type": "media_message",
        "message_id": str(message_id),
        "workspace_id": str(data.workspace_id),
        "phone_number_id": str(data.phone_number_id),
        "meta_phone_number_id": phone_number.phone_number_id,
        "from_number": phone_number.phone_number,
        "to_number": data.to,
        "media_type": data.media_type,
        "media_id": str(data.media_id),
        "media_url": sas_url,
        "mime_type": media.mime_type,
        "caption": data.caption,
        "sent_by": str(member.id),
    }

    success = await enqueue(Queue.OUTBOUND_MESSAGES, job)

    if not success:
        raise HTTPException(
            status_code=503,
            detail={"code": "QUEUE_ERROR", "message": "Failed to queue message for sending"},
        )

    log_event(
        "media_message_queued",
        message_id=str(message_id),
        workspace_id=str(data.workspace_id),
        media_type=data.media_type,
        to=data.to,
    )

    return MessageQueuedResponse(
        id=message_id,
        workspace_id=data.workspace_id,
        phone_number_id=data.phone_number_id,
        to_number=data.to,
        type=data.media_type,
        status=MessageStatus.PENDING.value,
        media_id=data.media_id,
        queued=True,
    )


@router.get("/{message_id}/status", response_model=MessageStatusResponse)
async def get_message_status(
    message_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Get message delivery status.
    
    Requires workspace membership.
    """
    result = await session.execute(
        select(Message).where(Message.id == message_id)
    )
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Verify workspace membership
    await get_workspace_member(message.workspace_id, current_user, session)

    return MessageStatusResponse(
        id=message.id,
        wa_message_id=message.wa_message_id,
        status=message.status,
        delivered_at=message.delivered_at.isoformat() if message.delivered_at else None,
        read_at=message.read_at.isoformat() if message.read_at else None,
    )
