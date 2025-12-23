"""
Campaign Management API endpoints.
"""

from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.db import get_async_session
from server.core.monitoring import log_event
from server.dependencies import User, get_current_user, get_workspace_member
from server.models.base import CampaignStatus, MessageStatus
from server.models.marketing import Campaign

router = APIRouter(prefix="/workspaces/{workspace_id}/campaigns", tags=["Campaigns"])

# Type aliases
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


# ============================================================================
# SCHEMAS
# ============================================================================


class CampaignContactAddRequest(BaseModel):
    contact_ids: list[UUID]
    filter_tags: Optional[list[str]] = None


class CampaignExecutionRequest(BaseModel):
    pass  # Future proofing


class CampaignCreate(BaseModel):
    workspace_id: Optional[UUID] = None  # Optional, overridden by path
    channel_id: UUID
    template_id: Optional[UUID] = None
    name: str = Field(..., min_length=1, max_length=255)


class CampaignUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[str] = None


class CampaignResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    channel_id: UUID
    template_id: Optional[UUID]
    name: str
    total_contacts: int
    sent_count: int
    delivered_count: int
    read_count: int
    failed_count: int
    status: str
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CampaignListResponse(BaseModel):
    data: list[CampaignResponse]
    total: int
    limit: int
    offset: int


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("", response_model=CampaignResponse, status_code=201)
async def create_campaign(
    workspace_id: UUID,
    data: CampaignCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Create a new campaign.
    """
    await get_workspace_member(workspace_id, current_user, session)

    campaign = Campaign(
        workspace_id=workspace_id,
        channel_id=data.channel_id,
        template_id=data.template_id,
        name=data.name,
        status=CampaignStatus.DRAFT.value,
    )

    session.add(campaign)
    await session.commit()
    await session.refresh(campaign)

    log_event(
        "campaign_created",
        campaign_id=str(campaign.id),
        workspace_id=str(workspace_id),
    )

    return campaign


@router.get("", response_model=CampaignListResponse)
async def list_campaigns(
    workspace_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
    status: Optional[str] = Query(None, description="Filter by status"),
    channel_id: Optional[UUID] = Query(None, description="Filter by channel"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List campaigns for a workspace.
    """
    await get_workspace_member(workspace_id, current_user, session)

    query = select(Campaign).where(
        Campaign.workspace_id == workspace_id,
        Campaign.deleted_at.is_(None),
    )

    if channel_id:
        query = query.where(Campaign.channel_id == channel_id)

    if status:
        query = query.where(Campaign.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Campaign.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(query)
    campaigns = result.scalars().all()

    return CampaignListResponse(
        data=[CampaignResponse.model_validate(c) for c in campaigns],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    workspace_id: UUID,
    campaign_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Get campaign details.
    """
    result = await session.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.workspace_id == workspace_id,
            Campaign.deleted_at.is_(None),
        )
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    await get_workspace_member(workspace_id, current_user, session)

    return campaign


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    workspace_id: UUID,
    campaign_id: UUID,
    data: CampaignUpdate,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Update campaign.
    """
    result = await session.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.workspace_id == workspace_id,
            Campaign.deleted_at.is_(None),
        )
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    await get_workspace_member(workspace_id, current_user, session)

    if data.name is not None:
        campaign.name = data.name

    if data.status is not None:
        valid_statuses = [s.value for s in CampaignStatus]
        if data.status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
            )
        campaign.status = data.status

    await session.commit()
    await session.refresh(campaign)

    log_event(
        "campaign_updated",
        campaign_id=str(campaign_id),
    )

    return campaign


@router.delete("/{campaign_id}", status_code=204)
async def delete_campaign(
    workspace_id: UUID,
    campaign_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Soft delete a campaign.
    """
    result = await session.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.workspace_id == workspace_id,
            Campaign.deleted_at.is_(None),
        )
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    await get_workspace_member(workspace_id, current_user, session)

    campaign.soft_delete()
    await session.commit()

    log_event(
        "campaign_deleted",
        campaign_id=str(campaign_id),
    )

    return None


@router.get("/{campaign_id}/contacts")
async def list_campaign_contacts(
    workspace_id: UUID,
    campaign_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
):
    """
    List contacts in a campaign with their status.
    """
    # Fetch campaign first to get workspace_id
    result = await session.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.workspace_id == workspace_id,
            Campaign.deleted_at.is_(None),
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    await get_workspace_member(workspace_id, current_user, session)

    from server.models.contacts import Contact
    from server.models.marketing import CampaignMessage

    query = (
        select(CampaignMessage, Contact)
        .join(Contact, CampaignMessage.contact_id == Contact.id)
        .where(CampaignMessage.campaign_id == campaign_id)
    )

    if status:
        query = query.where(CampaignMessage.status == status)

    # Get total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0

    # Paginate
    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    rows = result.all()

    data = []
    for msg, contact in rows:
        data.append(
            {
                "contact_id": contact.id,
                "phone_number": contact.phone_number,
                "name": contact.name,
                "status": msg.status,
                "encoded_message_id": msg.id,  # Useful for debugging
                "sent_at": msg.sent_at,
                "error_message": msg.error_message,
            }
        )

    return {"data": data, "total": total, "limit": limit, "offset": offset}


@router.post("/{campaign_id}/contacts", status_code=200)
async def add_campaign_contacts(
    workspace_id: UUID,
    campaign_id: UUID,
    data: CampaignContactAddRequest,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Add contacts to a draft campaign.
    Deduplicates contacts and filters by opt-in status.
    """
    result = await session.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.workspace_id == workspace_id,
            Campaign.deleted_at.is_(None),
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    await get_workspace_member(workspace_id, current_user, session)

    if campaign.status != CampaignStatus.DRAFT.value:
        raise HTTPException(
            status_code=400, detail="Contacts can only be added to DRAFT campaigns"
        )

    # Resolve contacts with per-channel opt-in validation
    from server.models.contacts import Contact, ContactChannelState

    # Get contacts that are opted-in for THIS channel
    query = (
        select(Contact)
        .join(
            ContactChannelState,
            (ContactChannelState.contact_id == Contact.id)
            & (ContactChannelState.channel_id == campaign.channel_id),
        )
        .where(
            Contact.workspace_id == campaign.workspace_id,
            Contact.deleted_at.is_(None),
            ContactChannelState.opt_in_status.is_(True),  # Per-channel opt-in check
            ContactChannelState.blocked.is_(False),  # Not blocked
        )
    )

    if data.contact_ids:
        query = query.where(Contact.id.in_(data.contact_ids))

    if data.filter_tags:
        # Simplistic tag filtering - improve based on actual tag implementation
        # Assuming tags are stored as JSON/Array or similar if we had a proper tag model
        # For now, skipping tag logic as it depends on implementation details
        pass

    result = await session.execute(query)
    contacts = result.scalars().all()

    added_count = 0
    from server.models.marketing import CampaignMessage

    # Bulk insert optimization opportunity here
    for contact in contacts:
        # Check if already exists
        exists = await session.execute(
            select(CampaignMessage).where(
                CampaignMessage.campaign_id == campaign_id,
                CampaignMessage.contact_id == contact.id,
            )
        )
        if exists.scalar_one_or_none():
            continue

        msg = CampaignMessage(
            workspace_id=campaign.workspace_id,
            campaign_id=campaign_id,
            contact_id=contact.id,
            channel_id=campaign.channel_id,
            status=MessageStatus.PENDING.value,
        )
        session.add(msg)
        added_count += 1

    if added_count > 0:
        campaign.total_contacts += added_count
        await session.commit()

    return {
        "message": f"Added {added_count} contacts",
        "total": campaign.total_contacts,
    }


@router.delete("/{campaign_id}/contacts", status_code=200)
async def remove_campaign_contacts(
    workspace_id: UUID,
    campaign_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Remove all PENDING contacts from a draft campaign.
    """
    result = await session.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.workspace_id == workspace_id,
            Campaign.deleted_at.is_(None),
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    await get_workspace_member(workspace_id, current_user, session)

    if campaign.status != CampaignStatus.DRAFT.value:
        raise HTTPException(
            status_code=400, detail="Contacts can only be removed from DRAFT campaigns"
        )

    from sqlalchemy import delete

    from server.models.marketing import CampaignMessage

    stmt = delete(CampaignMessage).where(
        CampaignMessage.campaign_id == campaign_id,
        CampaignMessage.status == MessageStatus.PENDING.value,
    )
    result = await session.execute(stmt)
    deleted = result.rowcount

    campaign.total_contacts = max(0, campaign.total_contacts - deleted)
    await session.commit()

    return {"message": f"Removed {deleted} pending contacts"}


@router.post("/{campaign_id}/execute", response_model=CampaignResponse)
async def execute_campaign(
    workspace_id: UUID,
    campaign_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Start campaign execution.
    Queues the campaign for processing.
    """
    result = await session.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.workspace_id == workspace_id,
            Campaign.deleted_at.is_(None),
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    await get_workspace_member(workspace_id, current_user, session)

    # Allow starting from DRAFT or SCHEDULED
    allowed_statuses = [CampaignStatus.DRAFT.value, CampaignStatus.SCHEDULED.value]
    if campaign.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Campaign must be DRAFT or SCHEDULED to start (current: {campaign.status})",
        )

    if campaign.total_contacts == 0:
        raise HTTPException(status_code=400, detail="Campaign has no contacts")

    # Update status to RUNNING
    campaign.status = CampaignStatus.RUNNING.value
    await session.commit()
    await session.refresh(campaign)

    # Queue job
    from server.core.redis import Queue, enqueue

    job = {
        "type": "execute_campaign",
        "campaign_id": str(campaign.id),
        "workspace_id": str(campaign.workspace_id),
    }

    success = await enqueue(Queue.CAMPAIGN_JOBS, job)

    if not success:
        # Rollback status if queue fails
        campaign.status = CampaignStatus.DRAFT.value
        await session.commit()
        raise HTTPException(
            status_code=503, detail="Failed to queue campaign execution"
        )

    log_event(
        "campaign_execution_started",
        campaign_id=str(campaign_id),
    )

    return campaign


@router.post("/{campaign_id}/pause", response_model=CampaignResponse)
async def pause_campaign(
    workspace_id: UUID,
    campaign_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Pause a running campaign.
    Changes status from RUNNING to SCHEDULED (resumable).
    """
    result = await session.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.workspace_id == workspace_id,
            Campaign.deleted_at.is_(None),
        )
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    await get_workspace_member(workspace_id, current_user, session)

    if campaign.status != CampaignStatus.RUNNING.value:
        raise HTTPException(
            status_code=400,
            detail=f"Campaign must be RUNNING to pause (current: {campaign.status})",
        )

    campaign.status = CampaignStatus.SCHEDULED.value
    await session.commit()
    await session.refresh(campaign)

    log_event(
        "campaign_paused",
        campaign_id=str(campaign_id),
    )

    return campaign


@router.post("/{campaign_id}/cancel", response_model=CampaignResponse)
async def cancel_campaign(
    workspace_id: UUID,
    campaign_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Cancel a running or scheduled campaign.
    Sets status to CANCELLED.
    """
    result = await session.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.workspace_id == workspace_id,
            Campaign.deleted_at.is_(None),
        )
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    await get_workspace_member(workspace_id, current_user, session)

    cancellable = [
        CampaignStatus.RUNNING.value,
        CampaignStatus.SCHEDULED.value,
        CampaignStatus.DRAFT.value,
    ]
    if campaign.status not in cancellable:
        raise HTTPException(
            status_code=400,
            detail=f"Campaign cannot be cancelled (current: {campaign.status})",
        )

    campaign.status = CampaignStatus.CANCELLED.value
    await session.commit()
    await session.refresh(campaign)

    log_event(
        "campaign_cancelled",
        campaign_id=str(campaign_id),
    )

    return campaign
