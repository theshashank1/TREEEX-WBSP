"""
Message Sending API endpoints for WhatsApp Business.
"""

import uuid as uuid_module
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.db import get_async_session
from server.core.monitoring import log_event
from server.core.redis import Queue, enqueue
from server.dependencies import (
    User,
    WorkspaceMember,
    WorkspaceMemberDep,
    get_current_user,
    get_workspace_member,
)
from server.models.base import MessageDirection, MessageStatus
from server.models.contacts import PhoneNumber
from server.models.messaging import MediaFile, Message
from server.schemas.messages import (
    MessageQueuedResponse,
    MessageResponse,
    MessageStatusResponse,
    SendMediaMessageRequest,
    SendTemplateMessageRequest,
    SendTextMessageRequest,
)
from server.services import azure_storage

router = APIRouter(prefix="/messages", tags=["Messages"])

# Type aliases for dependencies
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
# WorkspaceMemberDep = Annotated[WorkspaceMember, Depends(get_workspace_member)]


# ============================================================================
# CONSTANTS
# ============================================================================

# Valid media types
VALID_MEDIA_TYPES = {"image", "video", "audio", "document"}


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/send/text", response_model=MessageQueuedResponse, status_code=201)
async def send_text_message(
    data: SendTextMessageRequest,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Send a text message.

    Validates workspace membership and phone number,
    then queues the message for async delivery via WhatsApp API.

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

    if not phone_number.access_token:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "NO_ACCESS_TOKEN",
                "message": "Phone number has no access token configured",
            },
        )

    # Create message ID
    message_id = uuid_module.uuid4()

    # Queue the message for async sending
    job = {
        "type": "text_message",
        "message_id": str(message_id),
        "workspace_id": str(data.workspace_id),
        "phone_number_id": phone_number.phone_number_id,  # Meta's phone number ID
        "db_phone_number_id": str(data.phone_number_id),  # DB UUID for reference
        "from_number": phone_number.phone_number,
        "to_number": data.to,
        "text": data.text,
        "preview_url": False,
        "sent_by": str(member.id),
    }

    success = await enqueue(Queue.OUTBOUND_MESSAGES, job)

    if not success:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "QUEUE_ERROR",
                "message": "Failed to queue message for sending",
            },
        )

    log_event(
        "text_message_queued",
        message_id=str(message_id),
        workspace_id=str(data.workspace_id),
        to=data.to,
    )

    return MessageQueuedResponse(
        id=message_id,
        workspace_id=data.workspace_id,
        phone_number_id=data.phone_number_id,
        to_number=data.to,
        type="text",
        status=MessageStatus.PENDING.value,
        queued=True,
    )


@router.post("/send/template", response_model=MessageQueuedResponse, status_code=201)
async def send_template_message(
    data: SendTemplateMessageRequest,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Send a template message.

    Validates workspace membership and phone number,
    then queues the template message for async delivery via WhatsApp API.

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

    if not phone_number.access_token:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "NO_ACCESS_TOKEN",
                "message": "Phone number has no access token configured",
            },
        )

    # Create message ID
    message_id = uuid_module.uuid4()

    # Transform components from dict to list format if provided
    # Input: {"BODY": {"text": "..."}, "HEADER": {...}}
    # Output: [{"type": "body", "parameters": [...]}, {"type": "header", "parameters": [...]}]
    components_list = None
    if data.components:
        if isinstance(data.components, list):
            # If already a list, use as-is (standard format)
            components_list = data.components
        else:
            # If dict, transform to list (simplified format)
            # Input: {"BODY": {"text": "..."}, "HEADER": {...}}
            # Output: [{"type": "body", "parameters": [...]}, {"type": "header", "parameters": [...]}]
            components_list = []
            for component_type, component_data in data.components.items():
                # Convert component type to lowercase (BODY -> body, HEADER -> header)
                type_lower = component_type.lower()

                # Extract parameters based on component data structure
                parameters = []
                if isinstance(component_data, dict):
                    # If it has a "text" field, create a text parameter
                    if "text" in component_data:
                        parameters.append(
                            {"type": "text", "text": component_data["text"]}
                        )
                    # If it has "parameters" field already, use it directly
                    elif "parameters" in component_data:
                        parameters = component_data["parameters"]

                components_list.append({"type": type_lower, "parameters": parameters})

    # Queue the message for async sending
    job = {
        "type": "template_message",
        "message_id": str(message_id),
        "workspace_id": str(data.workspace_id),
        "phone_number_id": phone_number.phone_number_id,  # Meta's phone number ID
        "db_phone_number_id": str(data.phone_number_id),  # DB UUID for reference
        "from_number": phone_number.phone_number,
        "to_number": data.to,
        "template_name": data.template_name,
        "language_code": data.template_language,
        "components": components_list,
        "sent_by": str(member.id),
    }

    success = await enqueue(Queue.OUTBOUND_MESSAGES, job)

    if not success:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "QUEUE_ERROR",
                "message": "Failed to queue message for sending",
            },
        )

    log_event(
        "template_message_queued",
        message_id=str(message_id),
        workspace_id=str(data.workspace_id),
        template=data.template_name,
        to=data.to,
    )

    return MessageQueuedResponse(
        id=message_id,
        workspace_id=data.workspace_id,
        phone_number_id=data.phone_number_id,
        to_number=data.to,
        type="template",
        status=MessageStatus.PENDING.value,
        queued=True,
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
            detail={
                "code": "STORAGE_ERROR",
                "message": "Failed to parse media storage URL",
            },
        )

    sas_url = azure_storage.generate_sas_url(blob_name, expiry_minutes=30)
    if not sas_url:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "SAS_ERROR",
                "message": "Failed to generate media download URL",
            },
        )

    # Create a placeholder message record
    # Note: In a full implementation, this would create contact/conversation first
    message_id = uuid_module.uuid4()

    # Queue the message for async sending
    job = {
        "type": "media_message",
        "message_id": str(message_id),
        "workspace_id": str(data.workspace_id),
        "phone_number_id": phone_number.phone_number_id,  # Meta's phone number ID
        "db_phone_number_id": str(data.phone_number_id),  # DB UUID for reference
        "from_number": phone_number.phone_number,
        "to_number": data.to,
        "media_type": data.media_type,
        "media_id": str(data.media_id),
        "media_url": sas_url,  # Already a SAS URL
        "mime_type": media.mime_type,
        "caption": data.caption,
        "sent_by": str(member.id),
    }

    success = await enqueue(Queue.OUTBOUND_MESSAGES, job)

    if not success:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "QUEUE_ERROR",
                "message": "Failed to queue message for sending",
            },
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
    result = await session.execute(select(Message).where(Message.id == message_id))
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
