"""
Template Management API endpoints for WhatsApp Business.
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.db import get_async_session
from server.core.monitoring import log_event
from server.dependencies import User, get_current_user, get_workspace_member
from server.models.base import TemplateCategory, TemplateStatus
from server.models.contacts import PhoneNumber
from server.models.marketing import Template
from server.schemas.templates import (
    TemplateCreate,
    TemplateListResponse,
    TemplateResponse,
    TemplateUpdate,
)

router = APIRouter(prefix="/templates", tags=["Templates"])

# Type aliases for dependencies
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("", response_model=TemplateResponse, status_code=201)
async def create_template(
    data: TemplateCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Create a new WhatsApp message template.

    Templates must be approved by Meta before they can be used.
    The template will be created with PENDING status.

    Requires workspace membership.
    """
    # Verify workspace membership
    await get_workspace_member(data.workspace_id, current_user, session)

    # Validate category
    valid_categories = [c.value for c in TemplateCategory]
    if data.category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}",
        )

    # Verify phone number exists and belongs to workspace
    result = await session.execute(
        select(PhoneNumber).where(
            PhoneNumber.id == data.phone_number_id,
            PhoneNumber.workspace_id == data.workspace_id,
            PhoneNumber.deleted_at.is_(None),
        )
    )
    phone_number = result.scalar_one_or_none()

    if not phone_number:
        raise HTTPException(
            status_code=404,
            detail="Phone number not found or doesn't belong to workspace",
        )

    # Check if template with same name already exists for this phone number
    existing = await session.execute(
        select(Template).where(
            Template.workspace_id == data.workspace_id,
            Template.phone_number_id == data.phone_number_id,
            Template.name == data.name,
            Template.deleted_at.is_(None),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Template with this name already exists for this phone number",
        )

    # Create template
    template = Template(
        workspace_id=data.workspace_id,
        phone_number_id=data.phone_number_id,
        name=data.name,
        category=data.category,
        language=data.language,
        status=TemplateStatus.PENDING.value,
        components=data.components,
    )

    session.add(template)
    await session.commit()
    await session.refresh(template)

    log_event(
        "template_created",
        template_id=str(template.id),
        workspace_id=str(data.workspace_id),
        name=data.name,
    )

    return TemplateResponse(
        id=template.id,
        workspace_id=template.workspace_id,
        phone_number_id=template.phone_number_id,
        name=template.name,
        category=template.category,
        language=template.language,
        status=template.status,
        meta_template_id=template.meta_template_id,
        components=template.components,
        rejection_reason=template.rejection_reason,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.get("", response_model=TemplateListResponse)
async def list_templates(
    session: SessionDep,
    current_user: CurrentUserDep,
    workspace_id: UUID = Query(..., description="Workspace ID to filter by"),
    phone_number_id: Optional[UUID] = Query(None, description="Filter by phone number"),
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List templates for a workspace.

    Requires workspace membership.
    """
    # Verify workspace membership
    await get_workspace_member(workspace_id, current_user, session)

    # Build query
    query = select(Template).where(
        Template.workspace_id == workspace_id,
        Template.deleted_at.is_(None),
    )

    if phone_number_id:
        query = query.where(Template.phone_number_id == phone_number_id)

    if status:
        query = query.where(Template.status == status)

    if category:
        query = query.where(Template.category == category)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(Template.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(query)
    templates = result.scalars().all()

    return TemplateListResponse(
        data=[
            TemplateResponse(
                id=t.id,
                workspace_id=t.workspace_id,
                phone_number_id=t.phone_number_id,
                name=t.name,
                category=t.category,
                language=t.language,
                status=t.status,
                meta_template_id=t.meta_template_id,
                components=t.components,
                rejection_reason=t.rejection_reason,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in templates
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Get template details.

    Requires workspace membership.
    """
    result = await session.execute(
        select(Template).where(
            Template.id == template_id,
            Template.deleted_at.is_(None),
        )
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Verify workspace membership
    await get_workspace_member(template.workspace_id, current_user, session)

    return TemplateResponse(
        id=template.id,
        workspace_id=template.workspace_id,
        phone_number_id=template.phone_number_id,
        name=template.name,
        category=template.category,
        language=template.language,
        status=template.status,
        meta_template_id=template.meta_template_id,
        components=template.components,
        rejection_reason=template.rejection_reason,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.patch("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: UUID,
    data: TemplateUpdate,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Update template.

    Only components and status can be updated.
    Status changes are typically managed by Meta webhook updates.

    Requires workspace membership.
    """
    result = await session.execute(
        select(Template).where(
            Template.id == template_id,
            Template.deleted_at.is_(None),
        )
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Verify workspace membership
    await get_workspace_member(template.workspace_id, current_user, session)

    # Update fields
    if data.components is not None:
        template.components = data.components

    if data.status is not None:
        # Validate status is a valid TemplateStatus enum value
        valid_statuses = [s.value for s in TemplateStatus]
        if data.status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
            )
        template.status = data.status

    await session.commit()
    await session.refresh(template)

    log_event(
        "template_updated",
        template_id=str(template_id),
    )

    return TemplateResponse(
        id=template.id,
        workspace_id=template.workspace_id,
        phone_number_id=template.phone_number_id,
        name=template.name,
        category=template.category,
        language=template.language,
        status=template.status,
        meta_template_id=template.meta_template_id,
        components=template.components,
        rejection_reason=template.rejection_reason,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Soft delete a template.

    Requires workspace membership.
    """
    result = await session.execute(
        select(Template).where(
            Template.id == template_id,
            Template.deleted_at.is_(None),
        )
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Verify workspace membership
    await get_workspace_member(template.workspace_id, current_user, session)

    # Soft delete
    template.soft_delete()
    await session.commit()

    log_event(
        "template_deleted",
        template_id=str(template_id),
    )

    return None
