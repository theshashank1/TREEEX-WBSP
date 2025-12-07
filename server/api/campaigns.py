"""
Campaign Management API endpoints for WhatsApp Business.
"""
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.db import get_async_session
from server.core.monitoring import log_event
from server.dependencies import User, get_current_user, get_workspace_member
from server.models.base import CampaignStatus
from server.models.marketing import Campaign

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])

# Type aliases for dependencies
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


# ============================================================================
# SCHEMAS
# ============================================================================


class CampaignCreate(BaseModel):
    """Schema for creating a new campaign"""
    workspace_id: UUID
    phone_number_id: UUID
    template_id: Optional[UUID] = None
    name: str = Field(..., min_length=1, max_length=255)


class CampaignUpdate(BaseModel):
    """Schema for updating campaign"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[str] = None


class CampaignResponse(BaseModel):
    """Schema for campaign response"""
    id: UUID
    workspace_id: UUID
    phone_number_id: UUID
    template_id: Optional[UUID]
    name: str
    total_contacts: int
    sent_count: int
    delivered_count: int
    read_count: int
    failed_count: int
    status: str

    class Config:
        from_attributes = True


class CampaignListResponse(BaseModel):
    """Schema for paginated campaign list"""
    data: list[CampaignResponse]
    total: int
    limit: int
    offset: int


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("", response_model=CampaignResponse, status_code=201)
async def create_campaign(
    data: CampaignCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Create a new campaign.
    
    Requires workspace membership.
    """
    # Verify workspace membership
    await get_workspace_member(data.workspace_id, current_user, session)

    campaign = Campaign(
        workspace_id=data.workspace_id,
        phone_number_id=data.phone_number_id,
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
        workspace_id=str(data.workspace_id),
    )

    return campaign


@router.get("", response_model=CampaignListResponse)
async def list_campaigns(
    session: SessionDep,
    current_user: CurrentUserDep,
    workspace_id: UUID = Query(..., description="Workspace ID to filter by"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List campaigns for a workspace.
    
    Requires workspace membership.
    """
    # Verify workspace membership
    await get_workspace_member(workspace_id, current_user, session)

    # Build query
    query = select(Campaign).where(
        Campaign.workspace_id == workspace_id,
        Campaign.deleted_at.is_(None),
    )

    if status:
        query = query.where(Campaign.status == status)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
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
    campaign_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Get campaign details.
    
    Requires workspace membership.
    """
    result = await session.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.deleted_at.is_(None),
        )
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Verify workspace membership
    await get_workspace_member(campaign.workspace_id, current_user, session)

    return campaign


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    data: CampaignUpdate,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Update campaign.
    
    Requires workspace membership.
    """
    result = await session.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.deleted_at.is_(None),
        )
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Verify workspace membership
    await get_workspace_member(campaign.workspace_id, current_user, session)

    # Update fields
    if data.name is not None:
        campaign.name = data.name
    
    if data.status is not None:
        # Validate status is a valid CampaignStatus enum value
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
    campaign_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Soft delete a campaign.
    
    Requires workspace membership.
    """
    result = await session.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.deleted_at.is_(None),
        )
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Verify workspace membership
    await get_workspace_member(campaign.workspace_id, current_user, session)

    # Soft delete
    campaign.soft_delete()
    await session.commit()

    log_event(
        "campaign_deleted",
        campaign_id=str(campaign_id),
    )

    return None


@router.post("/{campaign_id}/start", response_model=CampaignResponse)
async def start_campaign(
    campaign_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Start a campaign.
    
    Changes status from DRAFT to ACTIVE.
    """
    result = await session.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.deleted_at.is_(None),
        )
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Verify workspace membership
    await get_workspace_member(campaign.workspace_id, current_user, session)

    if campaign.status != CampaignStatus.DRAFT.value:
        raise HTTPException(
            status_code=400,
            detail="Campaign must be in DRAFT status to start",
        )

    campaign.status = CampaignStatus.ACTIVE.value
    await session.commit()
    await session.refresh(campaign)

    log_event(
        "campaign_started",
        campaign_id=str(campaign_id),
    )

    return campaign


@router.post("/{campaign_id}/pause", response_model=CampaignResponse)
async def pause_campaign(
    campaign_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Pause an active campaign.
    
    Changes status from ACTIVE to PAUSED.
    """
    result = await session.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.deleted_at.is_(None),
        )
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Verify workspace membership
    await get_workspace_member(campaign.workspace_id, current_user, session)

    if campaign.status != CampaignStatus.ACTIVE.value:
        raise HTTPException(
            status_code=400,
            detail="Campaign must be ACTIVE to pause",
        )

    campaign.status = CampaignStatus.PAUSED.value
    await session.commit()
    await session.refresh(campaign)

    log_event(
        "campaign_paused",
        campaign_id=str(campaign_id),
    )

    return campaign
