"""
Media File Management API endpoints for WhatsApp Business.
"""
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.db import get_async_session
from server.core.monitoring import log_event
from server.dependencies import User, get_current_user, get_workspace_member
from server.models.messaging import MediaFile

router = APIRouter(prefix="/media", tags=["Media"])

# Type aliases for dependencies
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


# ============================================================================
# SCHEMAS
# ============================================================================


class MediaUploadRequest(BaseModel):
    """Schema for media upload request"""
    workspace_id: UUID
    type: str
    file_name: Optional[str] = None
    mime_type: Optional[str] = None


class MediaResponse(BaseModel):
    """Schema for media response"""
    id: UUID
    workspace_id: UUID
    type: str
    original_url: Optional[str]
    storage_url: Optional[str]
    file_name: Optional[str]
    file_size: Optional[int]
    mime_type: Optional[str]

    class Config:
        from_attributes = True


class MediaListResponse(BaseModel):
    """Schema for paginated media list"""
    data: list[MediaResponse]
    total: int
    limit: int
    offset: int


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("", response_model=MediaResponse, status_code=201)
async def upload_media(
    data: MediaUploadRequest,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Upload a media file.
    
    NOTE: This is a PLACEHOLDER endpoint for API scaffolding.
    Actual implementation should:
    1. Accept multipart/form-data file upload
    2. Upload to Azure Blob Storage
    3. Create MediaFile record with storage URLs
    
    Requires workspace membership.
    """
    # Verify workspace membership
    await get_workspace_member(data.workspace_id, current_user, session)

    # TODO: Implement actual file upload with multipart/form-data
    raise HTTPException(
        status_code=501,
        detail="Media upload not yet implemented. This is a placeholder endpoint.",
    )


@router.get("", response_model=MediaListResponse)
async def list_media(
    session: SessionDep,
    current_user: CurrentUserDep,
    workspace_id: UUID = Query(..., description="Workspace ID to filter by"),
    type: Optional[str] = Query(None, description="Filter by media type"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List media files for a workspace.
    
    Requires workspace membership.
    """
    # Verify workspace membership
    await get_workspace_member(workspace_id, current_user, session)

    # Build query
    query = select(MediaFile).where(
        MediaFile.workspace_id == workspace_id,
        MediaFile.deleted_at.is_(None),
    )

    if type:
        query = query.where(MediaFile.type == type)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(MediaFile.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(query)
    media_files = result.scalars().all()

    return MediaListResponse(
        data=[MediaResponse.model_validate(m) for m in media_files],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{media_id}", response_model=MediaResponse)
async def get_media(
    media_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Get media file details.
    
    Requires workspace membership.
    """
    result = await session.execute(
        select(MediaFile).where(
            MediaFile.id == media_id,
            MediaFile.deleted_at.is_(None),
        )
    )
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    # Verify workspace membership
    await get_workspace_member(media.workspace_id, current_user, session)

    return media


@router.delete("/{media_id}", status_code=204)
async def delete_media(
    media_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Soft delete a media file.
    
    Requires workspace membership.
    """
    result = await session.execute(
        select(MediaFile).where(
            MediaFile.id == media_id,
            MediaFile.deleted_at.is_(None),
        )
    )
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    # Verify workspace membership
    await get_workspace_member(media.workspace_id, current_user, session)

    # Soft delete
    media.soft_delete()
    await session.commit()

    log_event(
        "media_deleted",
        media_id=str(media_id),
    )

    return None
