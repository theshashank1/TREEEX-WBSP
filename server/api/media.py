"""
Media File Management API endpoints for WhatsApp Business.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.db import get_async_session
from server.core.monitoring import log_event, log_exception
from server.dependencies import User, get_current_user, get_workspace_member
from server.models.messaging import MediaFile
from server.services import azure_storage

router = APIRouter(prefix="/media", tags=["Media"])

# Type aliases for dependencies
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


# ============================================================================
# CONSTANTS
# ============================================================================

# File size limits in bytes
MAX_IMAGE_SIZE = 16 * 1024 * 1024  # 16 MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_AUDIO_SIZE = 16 * 1024 * 1024  # 16 MB
MAX_DOCUMENT_SIZE = 100 * 1024 * 1024  # 100 MB

# Allowed MIME types per category
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/bmp", "image/webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/3gpp", "video/quicktime"}
ALLOWED_AUDIO_TYPES = {"audio/aac", "audio/mp4", "audio/mpeg", "audio/amr", "audio/ogg"}
ALLOWED_DOCUMENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain",
}


# ============================================================================
# SCHEMAS
# ============================================================================


class MediaResponse(BaseModel):
    """Schema for media file response"""

    id: UUID
    workspace_id: UUID
    type: str
    original_url: Optional[str] = None
    storage_url: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MediaListResponse(BaseModel):
    """Schema for paginated media list"""

    data: list[MediaResponse]
    total: int
    limit: int
    offset: int


class MediaURLResponse(BaseModel):
    """Schema for temporary URL response"""

    url: str
    expires_in_minutes: int = Field(..., description="URL validity in minutes")
    expires_at: datetime = Field(..., description="Expiration timestamp")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_media_type(mime_type: str) -> Optional[str]:
    """Determine media type from MIME type."""
    if mime_type in ALLOWED_IMAGE_TYPES:
        return "image"
    elif mime_type in ALLOWED_VIDEO_TYPES:
        return "video"
    elif mime_type in ALLOWED_AUDIO_TYPES:
        return "audio"
    elif mime_type in ALLOWED_DOCUMENT_TYPES:
        return "document"
    return None


def get_max_size(media_type: str) -> int:
    """Get maximum file size for media type."""
    size_limits = {
        "image": MAX_IMAGE_SIZE,
        "video": MAX_VIDEO_SIZE,
        "audio": MAX_AUDIO_SIZE,
        "document": MAX_DOCUMENT_SIZE,
    }
    return size_limits.get(media_type, MAX_DOCUMENT_SIZE)


def format_size(size_bytes: int) -> str:
    """Format byte size to human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("", response_model=MediaResponse, status_code=201)
async def upload_media(
    session: SessionDep,
    current_user: CurrentUserDep,
    workspace_id: UUID = Form(..., description="Workspace ID"),
    file: UploadFile = File(..., description="File to upload"),
):
    """
    Upload a media file to Azure Blob Storage.

    Accepts multipart/form-data with:
    - workspace_id: UUID of the workspace
    - file: The file to upload

    File size limits:
    - Images: 16 MB (JPEG, PNG, GIF, BMP)
    - Videos: 100 MB (MP4, 3GPP, QuickTime)
    - Audio: 16 MB (AAC, MP4, MPEG, AMR, OGG)
    - Documents: 100 MB (PDF, Word, Excel, PowerPoint, Text)

    Requires workspace membership.
    """
    # Verify workspace membership
    member = await get_workspace_member(workspace_id, current_user, session)

    # Validate MIME type
    mime_type = file.content_type or "application/octet-stream"
    media_type = get_media_type(mime_type)

    if not media_type:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_FILE_TYPE",
                "message": f"Unsupported file type: {mime_type}",
                "allowed_types": {
                    "image": list(ALLOWED_IMAGE_TYPES),
                    "video": list(ALLOWED_VIDEO_TYPES),
                    "audio": list(ALLOWED_AUDIO_TYPES),
                    "document": list(ALLOWED_DOCUMENT_TYPES),
                },
            },
        )

    # Read file content
    try:
        file_data = await file.read()
    except Exception as e:
        log_exception("media_upload_read_error", e)
        raise HTTPException(
            status_code=400,
            detail={"code": "FILE_READ_ERROR", "message": "Failed to read file"},
        )

    # Validate file size
    file_size = len(file_data)
    max_size = get_max_size(media_type)

    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FILE_TOO_LARGE",
                "message": f"File size ({format_size(file_size)}) exceeds maximum "
                f"for {media_type} ({format_size(max_size)})",
            },
        )

    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail={"code": "EMPTY_FILE", "message": "File is empty"},
        )

    # Upload to Azure Blob Storage
    filename = file.filename or f"upload_{media_type}"
    blob_url, blob_name, error = await azure_storage.upload_file(
        file_data=file_data,
        filename=filename,
        mime_type=mime_type,
        workspace_id=str(workspace_id),
    )

    if error:
        log_event(
            "media_upload_azure_error",
            level="error",
            error=error,
            workspace_id=str(workspace_id),
        )
        raise HTTPException(
            status_code=500,
            detail={"code": "STORAGE_ERROR", "message": "Failed to upload file"},
        )

    # Create MediaFile record
    media_file = MediaFile(
        workspace_id=workspace_id,
        type=media_type,
        storage_url=blob_url,
        file_name=filename,
        file_size=file_size,
        mime_type=mime_type,
        uploaded_by=member.id,
    )

    session.add(media_file)
    await session.commit()
    await session.refresh(media_file)

    log_event(
        "media_uploaded",
        media_id=str(media_file.id),
        workspace_id=str(workspace_id),
        type=media_type,
        size=file_size,
        blob_name=blob_name,
    )

    return media_file


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


@router.get("/{media_id}/download")
async def download_media(
    media_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Download a media file via redirect to SAS URL.

    Returns a 307 redirect to a temporary Azure SAS URL (60 min expiry).
    This approach avoids streaming file bytes through the API server.

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

    if not media.storage_url:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "MEDIA_NOT_AVAILABLE",
                "message": "Media file has not been uploaded to storage yet",
            },
        )

    # Extract blob name from storage URL
    blob_name = azure_storage.extract_blob_name_from_url(media.storage_url)

    if not blob_name:
        log_event(
            "media_download_parse_error",
            level="error",
            media_id=str(media_id),
            storage_url=media.storage_url,
        )
        raise HTTPException(
            status_code=500,
            detail={"code": "URL_PARSE_ERROR", "message": "Failed to parse storage URL"},
        )

    # Generate SAS URL with 60 minute expiry
    sas_url = azure_storage.generate_sas_url(blob_name, expiry_minutes=60)

    if not sas_url:
        raise HTTPException(
            status_code=500,
            detail={"code": "SAS_GENERATION_ERROR", "message": "Failed to generate download URL"},
        )

    log_event(
        "media_download_redirect",
        media_id=str(media_id),
    )

    return RedirectResponse(url=sas_url, status_code=307)


@router.get("/{media_id}/url", response_model=MediaURLResponse)
async def get_media_url(
    media_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
    expiry_minutes: int = Query(60, ge=5, le=1440, description="URL validity in minutes"),
):
    """
    Get a temporary signed URL for a media file.

    Returns a JSON response with a temporary Azure SAS URL.
    Configurable expiry from 5 to 1440 minutes (24 hours).

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

    if not media.storage_url:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "MEDIA_NOT_AVAILABLE",
                "message": "Media file has not been uploaded to storage yet",
            },
        )

    # Extract blob name from storage URL
    blob_name = azure_storage.extract_blob_name_from_url(media.storage_url)

    if not blob_name:
        log_event(
            "media_url_parse_error",
            level="error",
            media_id=str(media_id),
            storage_url=media.storage_url,
        )
        raise HTTPException(
            status_code=500,
            detail={"code": "URL_PARSE_ERROR", "message": "Failed to parse storage URL"},
        )

    # Generate SAS URL with specified expiry
    sas_url = azure_storage.generate_sas_url(blob_name, expiry_minutes=expiry_minutes)

    if not sas_url:
        raise HTTPException(
            status_code=500,
            detail={"code": "SAS_GENERATION_ERROR", "message": "Failed to generate temporary URL"},
        )

    log_event(
        "media_url_generated",
        media_id=str(media_id),
        expiry_minutes=expiry_minutes,
    )

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)

    return MediaURLResponse(
        url=sas_url,
        expires_in_minutes=expiry_minutes,
        expires_at=expires_at,
    )


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
