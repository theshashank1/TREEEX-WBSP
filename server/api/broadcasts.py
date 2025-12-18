"""
Broadcast Messaging API endpoints for WhatsApp Business.
Supports creating and managing broadcasts to multiple contacts.
"""

from datetime import datetime, timezone
from typing import Annotated, List, Optional, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.db import get_async_session
from server.core.monitoring import log_event
from server.core.redis import Queue, enqueue
from server.dependencies import User, get_current_user, get_workspace_member
from server.models.contacts import Contact
from server.models.marketing import Broadcast, BroadcastStatus
from server.models.messaging import MediaFile

router = APIRouter(prefix="/broadcasts", tags=["Broadcasts"])

# Type aliases for dependencies
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


# ============================================================================
# CONSTANTS
# ============================================================================

# Maximum audience size
MAX_AUDIENCE_SIZE = 10000


# ============================================================================
# SCHEMAS
# ============================================================================


class BroadcastAudience(BaseModel):
    """Audience selection for broadcast - either contact IDs or label filters"""

    contact_ids: Optional[List[UUID]] = Field(
        None, description="List of specific contact IDs"
    )
    labels_filter: Optional[List[str]] = Field(
        None, description="List of labels to filter contacts"
    )

    @model_validator(mode="after")
    def validate_audience(self):
        if not self.contact_ids and not self.labels_filter:
            raise ValueError("Either contact_ids or labels_filter must be provided")
        if self.contact_ids and self.labels_filter:
            raise ValueError("Provide either contact_ids or labels_filter, not both")
        return self


class BroadcastCreate(BaseModel):
    """Schema for creating a new broadcast"""

    workspace_id: UUID
    phone_number_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    message_text: Optional[str] = Field(None, description="Text message content")
    media_id: Optional[UUID] = Field(None, description="Media file ID to attach")
    audience: BroadcastAudience
    scheduled_for: Optional[datetime] = Field(
        None, description="Schedule time (UTC). If not provided, broadcast is saved as draft."
    )

    @model_validator(mode="after")
    def validate_content(self):
        if not self.message_text and not self.media_id:
            raise ValueError("Either message_text or media_id must be provided")
        return self


class BroadcastResponse(BaseModel):
    """Schema for broadcast response"""

    id: UUID
    workspace_id: UUID
    phone_number_id: UUID
    name: str
    message_text: Optional[str]
    media_id: Optional[UUID]
    audience: dict
    status: str
    scheduled_for: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    total_recipients: int
    sent_count: int
    delivered_count: int
    read_count: int
    failed_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BroadcastListResponse(BaseModel):
    """Schema for paginated broadcast list"""

    data: List[BroadcastResponse]
    total: int
    limit: int
    offset: int


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("", response_model=BroadcastResponse, status_code=201)
async def create_broadcast(
    data: BroadcastCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Create a new broadcast.

    Supports targeting by:
    - contact_ids: List of specific contact UUIDs
    - labels_filter: List of labels to filter contacts

    Must provide either message_text or media_id (or both).

    If scheduled_for is provided:
    - Must be in the future
    - Status will be set to 'scheduled'

    If scheduled_for is not provided:
    - Status will be set to 'draft'

    Requires workspace membership.
    """
    # Verify workspace membership
    member = await get_workspace_member(data.workspace_id, current_user, session)

    # Validate scheduled time if provided
    if data.scheduled_for:
        now = datetime.now(timezone.utc)
        if data.scheduled_for.replace(tzinfo=timezone.utc) <= now:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_SCHEDULE",
                    "message": "Scheduled time must be in the future",
                },
            )

    # Validate media if provided
    if data.media_id:
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
                    "message": "Media file is not yet uploaded to storage",
                },
            )

    # Validate audience size
    audience_dict = data.audience.model_dump(exclude_none=True)
    recipient_count = 0

    if data.audience.contact_ids:
        if len(data.audience.contact_ids) > MAX_AUDIENCE_SIZE:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "AUDIENCE_TOO_LARGE",
                    "message": f"Maximum audience size is {MAX_AUDIENCE_SIZE} contacts",
                },
            )
        recipient_count = len(data.audience.contact_ids)

    elif data.audience.labels_filter:
        # Count contacts matching labels
        count_query = select(func.count()).select_from(
            select(Contact)
            .where(
                and_(
                    Contact.workspace_id == data.workspace_id,
                    Contact.deleted_at.is_(None),
                    Contact.opted_in.is_(True),
                    Contact.tags.overlap(data.audience.labels_filter),
                )
            )
            .subquery()
        )
        result = await session.execute(count_query)
        recipient_count = result.scalar() or 0

        if recipient_count > MAX_AUDIENCE_SIZE:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "AUDIENCE_TOO_LARGE",
                    "message": f"Label filter matches {recipient_count} contacts. Maximum is {MAX_AUDIENCE_SIZE}.",
                },
            )

        if recipient_count == 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "EMPTY_AUDIENCE",
                    "message": "No contacts match the specified labels filter",
                },
            )

    # Determine status
    status = BroadcastStatus.DRAFT
    if data.scheduled_for:
        status = BroadcastStatus.SCHEDULED

    # Create broadcast
    broadcast = Broadcast(
        workspace_id=data.workspace_id,
        phone_number_id=data.phone_number_id,
        name=data.name,
        message_text=data.message_text,
        media_id=data.media_id,
        audience=audience_dict,
        status=status,
        scheduled_for=data.scheduled_for,
        total_recipients=recipient_count,
        created_by=member.id,
    )

    session.add(broadcast)
    await session.commit()
    await session.refresh(broadcast)

    log_event(
        "broadcast_created",
        broadcast_id=str(broadcast.id),
        workspace_id=str(data.workspace_id),
        status=status,
        recipients=recipient_count,
    )

    return broadcast


@router.get("", response_model=BroadcastListResponse)
async def list_broadcasts(
    session: SessionDep,
    current_user: CurrentUserDep,
    workspace_id: UUID = Query(..., description="Workspace ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List broadcasts for a workspace.

    Requires workspace membership.
    """
    # Verify workspace membership
    await get_workspace_member(workspace_id, current_user, session)

    # Build query
    query = select(Broadcast).where(
        Broadcast.workspace_id == workspace_id,
        Broadcast.deleted_at.is_(None),
    )

    if status:
        query = query.where(Broadcast.status == status)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(Broadcast.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(query)
    broadcasts = result.scalars().all()

    return BroadcastListResponse(
        data=[BroadcastResponse.model_validate(b) for b in broadcasts],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{broadcast_id}", response_model=BroadcastResponse)
async def get_broadcast(
    broadcast_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Get broadcast details.

    Requires workspace membership.
    """
    result = await session.execute(
        select(Broadcast).where(
            Broadcast.id == broadcast_id,
            Broadcast.deleted_at.is_(None),
        )
    )
    broadcast = result.scalar_one_or_none()

    if not broadcast:
        raise HTTPException(status_code=404, detail="Broadcast not found")

    # Verify workspace membership
    await get_workspace_member(broadcast.workspace_id, current_user, session)

    return broadcast


@router.post("/{broadcast_id}/cancel", response_model=BroadcastResponse)
async def cancel_broadcast(
    broadcast_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Cancel a broadcast.

    Can only cancel broadcasts in 'draft' or 'scheduled' status.
    Cannot cancel broadcasts that are already 'sending', 'completed', or 'failed'.

    Requires workspace membership.
    """
    result = await session.execute(
        select(Broadcast).where(
            Broadcast.id == broadcast_id,
            Broadcast.deleted_at.is_(None),
        )
    )
    broadcast = result.scalar_one_or_none()

    if not broadcast:
        raise HTTPException(status_code=404, detail="Broadcast not found")

    # Verify workspace membership
    await get_workspace_member(broadcast.workspace_id, current_user, session)

    # Check if broadcast can be canceled
    if broadcast.status not in [BroadcastStatus.DRAFT, BroadcastStatus.SCHEDULED]:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "CANNOT_CANCEL",
                "message": f"Cannot cancel broadcast with status '{broadcast.status}'",
            },
        )

    broadcast.status = BroadcastStatus.CANCELED
    await session.commit()
    await session.refresh(broadcast)

    log_event(
        "broadcast_canceled",
        broadcast_id=str(broadcast_id),
    )

    return broadcast


@router.post("/{broadcast_id}/send", response_model=BroadcastResponse)
async def send_broadcast(
    broadcast_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Start sending a broadcast immediately.

    Can only send broadcasts in 'draft' or 'scheduled' status.

    Requires workspace membership.
    """
    result = await session.execute(
        select(Broadcast).where(
            Broadcast.id == broadcast_id,
            Broadcast.deleted_at.is_(None),
        )
    )
    broadcast = result.scalar_one_or_none()

    if not broadcast:
        raise HTTPException(status_code=404, detail="Broadcast not found")

    # Verify workspace membership
    await get_workspace_member(broadcast.workspace_id, current_user, session)

    # Check if broadcast can be sent
    if broadcast.status not in [BroadcastStatus.DRAFT, BroadcastStatus.SCHEDULED]:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "CANNOT_SEND",
                "message": f"Cannot send broadcast with status '{broadcast.status}'",
            },
        )

    # Update status to sending
    broadcast.status = BroadcastStatus.SENDING
    broadcast.started_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await session.commit()
    await session.refresh(broadcast)

    # Queue broadcast job
    await enqueue(
        Queue.CAMPAIGN_JOBS,
        {
            "type": "broadcast",
            "broadcast_id": str(broadcast.id),
            "workspace_id": str(broadcast.workspace_id),
        },
    )

    log_event(
        "broadcast_started",
        broadcast_id=str(broadcast_id),
    )

    return broadcast


@router.delete("/{broadcast_id}", status_code=204)
async def delete_broadcast(
    broadcast_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Soft delete a broadcast.

    Can only delete broadcasts in 'draft', 'completed', 'canceled', or 'failed' status.
    Cannot delete broadcasts that are 'scheduled' or 'sending'.

    Requires workspace membership.
    """
    result = await session.execute(
        select(Broadcast).where(
            Broadcast.id == broadcast_id,
            Broadcast.deleted_at.is_(None),
        )
    )
    broadcast = result.scalar_one_or_none()

    if not broadcast:
        raise HTTPException(status_code=404, detail="Broadcast not found")

    # Verify workspace membership
    await get_workspace_member(broadcast.workspace_id, current_user, session)

    # Check if broadcast can be deleted
    if broadcast.status in [BroadcastStatus.SCHEDULED, BroadcastStatus.SENDING]:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "CANNOT_DELETE",
                "message": f"Cannot delete broadcast with status '{broadcast.status}'. Cancel it first.",
            },
        )

    # Soft delete
    broadcast.soft_delete()
    await session.commit()

    log_event(
        "broadcast_deleted",
        broadcast_id=str(broadcast_id),
    )

    return None
