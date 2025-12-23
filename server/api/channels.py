"""
Channel API endpoints for WhatsApp Business.
"""

from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.db import get_async_session
from server.core.monitoring import log_event, log_exception
from server.dependencies import (
    User,
    WorkspaceMember,
    get_current_user,
    get_workspace_member,
    require_workspace_admin,
)
from server.models.base import (
    MemberRole,
    PhoneNumberQuality,
    PhoneNumberStatus,
    utc_now,
)
from server.models.contacts import Channel
from server.schemas.channels import (
    ErrorDetail,
    ChannelCreate,
    ChannelListResponse,
    ChannelResponse,
    ChannelSyncResponse,
    ChannelUpdate,
)
from server.whatsapp.client import WhatsAppClient

router = APIRouter(
    prefix="/workspaces/{workspace_id}/channels", tags=["Channels"]
)

# Type aliases for dependencies
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


def _channel_to_response(channel: Channel) -> ChannelResponse:
    """Convert Channel model to response schema."""
    return ChannelResponse(
        id=channel.id,
        workspace_id=channel.workspace_id,
        phone_number=channel.phone_number,
        meta_phone_number_id=channel.meta_phone_number_id,
        display_name=channel.display_name,
        meta_business_id=channel.meta_business_id,
        quality_rating=channel.quality_rating,
        message_limit=channel.message_limit,
        tier=channel.tier,
        status=channel.status,
        verified_at=channel.verified_at,
        created_at=channel.created_at,
        updated_at=channel.updated_at,
    )


@router.post("", response_model=ChannelResponse, status_code=201)
async def create_channel(
    workspace_id: UUID,
    data: ChannelCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Register a new WhatsApp Channel.

    Flow:
    1. Verify workspace membership (OWNER or ADMIN)
    2. Validate access_token with Meta API
    3. Fetch phone number details from Meta
    4. Check if meta_phone_number_id already exists
    5. Create Channel record
    6. Return ChannelResponse
    """
    # Verify user has admin access to workspace
    member = await require_workspace_admin(workspace_id, current_user, session)

    # Force workspace_id from path
    data.workspace_id = workspace_id

    # Initialize WhatsApp client
    wa_client = WhatsAppClient(access_token=data.access_token)

    # Validate access token
    is_valid, token_error = await wa_client.validate_token()
    if not is_valid:
        log_event(
            "channel_create_failed",
            level="warning",
            workspace_id=str(workspace_id),
            error_code=token_error.code if token_error else "unknown",
            error_message=token_error.message if token_error else "unknown",
        )

        # Determine error code based on Meta API error
        error_code = "INVALID_TOKEN"
        if token_error and token_error.code == 10:
            error_code = "TOKEN_PERMISSION_DENIED"

        raise HTTPException(
            status_code=400,
            detail={
                "code": error_code,
                "message": (
                    token_error.message
                    if token_error
                    else "The access token is invalid or expired."
                ),
            },
        )

    # Fetch phone number details from Meta
    # Note: wa_client.get_phone_number expects meta_phone_number_id string
    phone_info, phone_error = await wa_client.get_phone_number(data.meta_phone_number_id)
    if not phone_info:
        log_event(
            "channel_create_failed",
            level="warning",
            workspace_id=str(workspace_id),
            meta_phone_number_id=data.meta_phone_number_id,
            error_code=phone_error.code if phone_error else "unknown",
        )
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_PHONE_NUMBER_ID",
                "message": (
                    phone_error.message
                    if phone_error
                    else "Phone number ID doesn't exist in Meta."
                ),
            },
        )

    # Check if meta_phone_number_id already exists
    existing = await session.execute(
        select(Channel).where(
            Channel.meta_phone_number_id == data.meta_phone_number_id,
            Channel.deleted_at.is_(None),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail={
                "code": "CHANNEL_EXISTS",
                "message": "This phone number/channel is already registered.",
            },
        )

    # Create Channel record
    now = utc_now()
    channel = Channel(
        workspace_id=workspace_id,
        phone_number=phone_info.phone_number,
        meta_phone_number_id=data.meta_phone_number_id,
        display_name=data.display_name or phone_info.verified_name,
        access_token=data.access_token,
        meta_business_id=data.meta_business_id,
        quality_rating=phone_info.quality_rating or PhoneNumberQuality.UNKNOWN.value,
        message_limit=WhatsAppClient.parse_message_limit(
            phone_info.messaging_limit_tier
        ),
        tier=phone_info.messaging_limit_tier,
        status=PhoneNumberStatus.ACTIVE.value,
        verified_at=now,
    )

    session.add(channel)
    await session.commit()
    await session.refresh(channel)

    log_event(
        "channel_created",
        level="info",
        workspace_id=str(workspace_id),
        meta_phone_number_id=data.meta_phone_number_id,
        phone_number=phone_info.phone_number,
    )

    return _channel_to_response(channel)


@router.get("", response_model=ChannelListResponse)
async def list_channels(
    workspace_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
    status: Optional[str] = Query(
        None, description="Filter by status (pending, active, disabled)"
    ),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """
    List channels for a workspace.

    Requires workspace membership.
    """
    # Verify workspace membership
    await get_workspace_member(workspace_id, current_user, session)

    # Build query
    query = select(Channel).where(
        Channel.workspace_id == workspace_id,
        Channel.deleted_at.is_(None),
    )

    if status:
        query = query.where(Channel.status == status)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(Channel.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(query)
    channels = result.scalars().all()

    return ChannelListResponse(
        data=[_channel_to_response(p) for p in channels],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    workspace_id: UUID,
    channel_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Get details of a specific channel.

    Requires workspace membership.
    """
    # Fetch channel
    result = await session.execute(
        select(Channel).where(
            Channel.id == channel_id,
            Channel.workspace_id == workspace_id,
            Channel.deleted_at.is_(None),
        )
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Channel not found."},
        )

    # Verify workspace membership
    await get_workspace_member(workspace_id, current_user, session)

    return _channel_to_response(channel)


@router.patch("/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    workspace_id: UUID,
    channel_id: UUID,
    data: ChannelUpdate,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Update channel settings.

    Requires OWNER or ADMIN role.
    """
    # Fetch channel
    result = await session.execute(
        select(Channel).where(
            Channel.id == channel_id,
            Channel.workspace_id == workspace_id,
            Channel.deleted_at.is_(None),
        )
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Channel not found."},
        )

    # Verify admin access
    await require_workspace_admin(workspace_id, current_user, session)

    # Validate new access token if provided
    if data.access_token:
        wa_client = WhatsAppClient(access_token=data.access_token)
        is_valid, token_error = await wa_client.validate_token()
        if not is_valid:
            error_code = "INVALID_TOKEN"
            if token_error and token_error.code == 10:
                error_code = "TOKEN_PERMISSION_DENIED"
            raise HTTPException(
                status_code=400,
                detail={
                    "code": error_code,
                    "message": (
                        token_error.message
                        if token_error
                        else "The access token is invalid or expired."
                    ),
                },
            )
        channel.access_token = data.access_token

    # Update fields
    if data.display_name is not None:
        channel.display_name = data.display_name

    if data.status is not None:
        if data.status not in [s.value for s in PhoneNumberStatus]:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_STATUS",
                    "message": f"Invalid status. Must be one of: {', '.join(s.value for s in PhoneNumberStatus)}",
                },
            )
        channel.status = data.status

    await session.commit()
    await session.refresh(channel)

    log_event(
        "channel_updated",
        level="info",
        channel_id=str(channel_id),
        workspace_id=str(channel.workspace_id),
    )

    return _channel_to_response(channel)


@router.delete("/{channel_id}", status_code=204)
async def delete_channel(
    workspace_id: UUID,
    channel_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Soft delete a channel.

    Requires OWNER or ADMIN role.
    """
    # Fetch channel
    result = await session.execute(
        select(Channel).where(
            Channel.id == channel_id,
            Channel.workspace_id == workspace_id,
            Channel.deleted_at.is_(None),
        )
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Channel not found."},
        )

    # Verify admin access
    await require_workspace_admin(workspace_id, current_user, session)

    # Soft delete
    channel.soft_delete()
    await session.commit()

    log_event(
        "channel_deleted",
        level="info",
        channel_id=str(channel_id),
        workspace_id=str(channel.workspace_id),
    )

    return None


@router.post("/{channel_id}/sync", response_model=ChannelSyncResponse)
async def sync_channel(
    workspace_id: UUID,
    channel_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Sync channel data from Meta API.

    Fetches the latest quality rating, message limit, and tier from Meta.
    Requires workspace membership.
    """
    # Fetch channel
    result = await session.execute(
        select(Channel).where(
            Channel.id == channel_id,
            Channel.workspace_id == workspace_id,
            Channel.deleted_at.is_(None),
        )
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Channel not found."},
        )

    # Verify workspace membership
    await get_workspace_member(workspace_id, current_user, session)

    # Fetch from Meta API
    wa_client = WhatsAppClient(access_token=channel.access_token)
    phone_info, phone_error = await wa_client.get_phone_number(
        channel.meta_phone_number_id
    )

    if not phone_info:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "SYNC_FAILED",
                "message": (
                    phone_error.message
                    if phone_error
                    else "Failed to sync from Meta API."
                ),
            },
        )

    # Update channel with fresh data
    channel.quality_rating = (
        phone_info.quality_rating or PhoneNumberQuality.UNKNOWN.value
    )
    channel.tier = phone_info.messaging_limit_tier
    channel.message_limit = WhatsAppClient.parse_message_limit(
        phone_info.messaging_limit_tier
    )

    now = utc_now()
    await session.commit()
    await session.refresh(channel)

    log_event(
        "channel_synced",
        level="info",
        channel_id=str(channel_id),
        quality_rating=channel.quality_rating,
    )

    return ChannelSyncResponse(
        id=channel.id,
        synced_at=now,
        phone_number=channel.phone_number,
        quality_rating=channel.quality_rating,
        message_limit=channel.message_limit,
        tier=channel.tier,
        status=channel.status,
    )


@router.post("/{channel_id}/exchange-token", response_model=ChannelResponse)
async def exchange_token_for_long_term(
    workspace_id: UUID,
    channel_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Exchange short-lived access token for long-lived token.

    Expires in ~60 days. System user tokens don't need this.
    Requires workspace admin access.
    """
    # Fetch channel
    result = await session.execute(
        select(Channel).where(
            Channel.id == channel_id,
            Channel.workspace_id == workspace_id,
            Channel.deleted_at.is_(None),
        )
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Channel not found."},
        )

    # Verify admin access
    await require_workspace_admin(workspace_id, current_user, session)

    # Exchange token
    wa_client = WhatsAppClient(access_token=channel.access_token)
    long_lived_token, error = await wa_client.exchange_token_for_long_term()

    if not long_lived_token:
        log_event(
            "token_exchange_failed",
            level="warning",
            channel_id=str(channel_id),
            error_code=error.code if error else "unknown",
        )
        raise HTTPException(
            status_code=400,
            detail={
                "code": "TOKEN_EXCHANGE_FAILED",
                "message": (
                    error.message
                    if error
                    else "Failed to exchange token for long-lived token."
                ),
            },
        )

    # Update channel with new long-lived token
    channel.access_token = long_lived_token
    await session.commit()
    await session.refresh(channel)

    log_event(
        "token_exchanged",
        level="info",
        channel_id=str(channel_id),
    )

    return _channel_to_response(channel)
