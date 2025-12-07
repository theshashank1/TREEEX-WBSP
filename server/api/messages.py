"""
Message Sending API endpoints for WhatsApp Business.
"""
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.db import get_async_session
from server.core.monitoring import log_event
from server.dependencies import User, get_current_user, get_workspace_member
from server.models.base import MessageDirection, MessageStatus
from server.models.contacts import PhoneNumber
from server.models.messaging import Message

router = APIRouter(prefix="/messages", tags=["Messages"])

# Type aliases for dependencies
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


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
    media_id: Optional[UUID] = None
    caption: Optional[str] = None


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


@router.post("/send/media", response_model=MessageResponse, status_code=201)
async def send_media_message(
    data: SendMediaMessageRequest,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Send a media message.
    
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

    # TODO: Implement actual media message sending
    raise HTTPException(
        status_code=501,
        detail="Media message sending not yet implemented. This is a placeholder endpoint.",
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
