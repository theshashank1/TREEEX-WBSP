"""
Phone Number API endpoints for WhatsApp Business.
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
from server.models.base import MemberRole, PhoneNumberQuality, PhoneNumberStatus, utc_now
from server.models.contacts import PhoneNumber
from server.schemas.phone_numbers import (
    ErrorDetail,
    PhoneNumberCreate,
    PhoneNumberListResponse,
    PhoneNumberResponse,
    PhoneNumberSyncResponse,
    PhoneNumberUpdate,
)
from server.whatsapp.client import WhatsAppClient

router = APIRouter(prefix="/phone-numbers", tags=["Phone Numbers"])

# Type aliases for dependencies
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


def _phone_number_to_response(phone: PhoneNumber) -> PhoneNumberResponse:
    """Convert PhoneNumber model to response schema."""
    return PhoneNumberResponse(
        id=phone.id,
        workspace_id=phone.workspace_id,
        phone_number=phone.phone_number,
        phone_number_id=phone.phone_number_id,
        display_name=phone.display_name,
        business_id=phone.business_id,
        quality_rating=phone.quality_rating,
        message_limit=phone.message_limit,
        tier=phone.tier,
        status=phone.status,
        verified_at=phone.verified_at,
        created_at=phone.created_at,
        updated_at=phone.updated_at,
    )


@router.post("", response_model=PhoneNumberResponse, status_code=201)
async def create_phone_number(
    data: PhoneNumberCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Register a new WhatsApp Business phone number.

    Flow:
    1. Verify workspace membership (OWNER or ADMIN)
    2. Validate access_token with Meta API
    3. Fetch phone number details from Meta
    4. Check if phone_number_id already exists
    5. Create PhoneNumber record
    6. Return PhoneNumberResponse
    """
    # Verify user has admin access to workspace
    member = await require_workspace_admin(data.workspace_id, current_user, session)

    # Initialize WhatsApp client
    wa_client = WhatsAppClient(access_token=data.access_token)

    # Validate access token
    is_valid, token_error = await wa_client.validate_token()
    if not is_valid:
        log_event(
            "phone_number_create_failed",
            level="warning",
            workspace_id=str(data.workspace_id),
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
                "message": token_error.message if token_error else "The access token is invalid or expired.",
            },
        )

    # Fetch phone number details from Meta
    phone_info, phone_error = await wa_client.get_phone_number(data.phone_number_id)
    if not phone_info:
        log_event(
            "phone_number_create_failed",
            level="warning",
            workspace_id=str(data.workspace_id),
            phone_number_id=data.phone_number_id,
            error_code=phone_error.code if phone_error else "unknown",
        )
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_PHONE_NUMBER_ID",
                "message": phone_error.message if phone_error else "Phone number ID doesn't exist in Meta.",
            },
        )

    # Check if phone_number_id already exists
    existing = await session.execute(
        select(PhoneNumber).where(
            PhoneNumber.phone_number_id == data.phone_number_id,
            PhoneNumber.deleted_at.is_(None),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail={
                "code": "PHONE_NUMBER_EXISTS",
                "message": "This phone number is already registered.",
            },
        )

    # Create PhoneNumber record
    now = utc_now()
    phone_number = PhoneNumber(
        workspace_id=data.workspace_id,
        phone_number=phone_info.phone_number,
        phone_number_id=data.phone_number_id,
        display_name=data.display_name or phone_info.verified_name,
        access_token=data.access_token,
        business_id=data.business_id,
        quality_rating=phone_info.quality_rating or PhoneNumberQuality.UNKNOWN.value,
        message_limit=WhatsAppClient.parse_message_limit(phone_info.messaging_limit_tier),
        tier=phone_info.messaging_limit_tier,
        status=PhoneNumberStatus.ACTIVE.value,
        verified_at=now,
    )

    session.add(phone_number)
    await session.commit()
    await session.refresh(phone_number)

    log_event(
        "phone_number_created",
        level="info",
        workspace_id=str(data.workspace_id),
        phone_number_id=data.phone_number_id,
        phone_number=phone_info.phone_number,
    )

    return _phone_number_to_response(phone_number)


@router.get("", response_model=PhoneNumberListResponse)
async def list_phone_numbers(
    session: SessionDep,
    current_user: CurrentUserDep,
    workspace_id: UUID = Query(..., description="Workspace ID to filter by"),
    status: Optional[str] = Query(None, description="Filter by status (pending, active, disabled)"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """
    List phone numbers for a workspace.

    Requires workspace membership.
    """
    # Verify workspace membership
    await get_workspace_member(workspace_id, current_user, session)

    # Build query
    query = select(PhoneNumber).where(
        PhoneNumber.workspace_id == workspace_id,
        PhoneNumber.deleted_at.is_(None),
    )

    if status:
        query = query.where(PhoneNumber.status == status)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(PhoneNumber.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(query)
    phone_numbers = result.scalars().all()

    return PhoneNumberListResponse(
        data=[_phone_number_to_response(p) for p in phone_numbers],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{phone_number_id}", response_model=PhoneNumberResponse)
async def get_phone_number(
    phone_number_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Get details of a specific phone number.

    Requires workspace membership.
    """
    # Fetch phone number
    result = await session.execute(
        select(PhoneNumber).where(
            PhoneNumber.id == phone_number_id,
            PhoneNumber.deleted_at.is_(None),
        )
    )
    phone_number = result.scalar_one_or_none()

    if not phone_number:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Phone number not found."},
        )

    # Verify workspace membership
    await get_workspace_member(phone_number.workspace_id, current_user, session)

    return _phone_number_to_response(phone_number)


@router.patch("/{phone_number_id}", response_model=PhoneNumberResponse)
async def update_phone_number(
    phone_number_id: UUID,
    data: PhoneNumberUpdate,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Update phone number settings.

    Requires OWNER or ADMIN role.
    """
    # Fetch phone number
    result = await session.execute(
        select(PhoneNumber).where(
            PhoneNumber.id == phone_number_id,
            PhoneNumber.deleted_at.is_(None),
        )
    )
    phone_number = result.scalar_one_or_none()

    if not phone_number:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Phone number not found."},
        )

    # Verify admin access
    await require_workspace_admin(phone_number.workspace_id, current_user, session)

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
                    "message": token_error.message if token_error else "The access token is invalid or expired.",
                },
            )
        phone_number.access_token = data.access_token

    # Update fields
    if data.display_name is not None:
        phone_number.display_name = data.display_name

    if data.status is not None:
        if data.status not in [s.value for s in PhoneNumberStatus]:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_STATUS",
                    "message": f"Invalid status. Must be one of: {', '.join(s.value for s in PhoneNumberStatus)}",
                },
            )
        phone_number.status = data.status

    await session.commit()
    await session.refresh(phone_number)

    log_event(
        "phone_number_updated",
        level="info",
        phone_number_id=str(phone_number_id),
        workspace_id=str(phone_number.workspace_id),
    )

    return _phone_number_to_response(phone_number)


@router.delete("/{phone_number_id}", status_code=204)
async def delete_phone_number(
    phone_number_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Soft delete a phone number.

    Requires OWNER or ADMIN role.
    """
    # Fetch phone number
    result = await session.execute(
        select(PhoneNumber).where(
            PhoneNumber.id == phone_number_id,
            PhoneNumber.deleted_at.is_(None),
        )
    )
    phone_number = result.scalar_one_or_none()

    if not phone_number:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Phone number not found."},
        )

    # Verify admin access
    await require_workspace_admin(phone_number.workspace_id, current_user, session)

    # Soft delete
    phone_number.soft_delete()
    await session.commit()

    log_event(
        "phone_number_deleted",
        level="info",
        phone_number_id=str(phone_number_id),
        workspace_id=str(phone_number.workspace_id),
    )

    return None


@router.post("/{phone_number_id}/sync", response_model=PhoneNumberSyncResponse)
async def sync_phone_number(
    phone_number_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Sync phone number data from Meta API.

    Fetches the latest quality rating, message limit, and tier from Meta.
    Requires workspace membership.
    """
    # Fetch phone number
    result = await session.execute(
        select(PhoneNumber).where(
            PhoneNumber.id == phone_number_id,
            PhoneNumber.deleted_at.is_(None),
        )
    )
    phone_number = result.scalar_one_or_none()

    if not phone_number:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Phone number not found."},
        )

    # Verify workspace membership
    await get_workspace_member(phone_number.workspace_id, current_user, session)

    # Fetch from Meta API
    wa_client = WhatsAppClient(access_token=phone_number.access_token)
    phone_info, phone_error = await wa_client.get_phone_number(phone_number.phone_number_id)

    if not phone_info:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "SYNC_FAILED",
                "message": phone_error.message if phone_error else "Failed to sync from Meta API.",
            },
        )

    # Update phone number with fresh data
    phone_number.quality_rating = phone_info.quality_rating or PhoneNumberQuality.UNKNOWN.value
    phone_number.tier = phone_info.messaging_limit_tier
    phone_number.message_limit = WhatsAppClient.parse_message_limit(phone_info.messaging_limit_tier)

    now = utc_now()
    await session.commit()
    await session.refresh(phone_number)

    log_event(
        "phone_number_synced",
        level="info",
        phone_number_id=str(phone_number_id),
        quality_rating=phone_number.quality_rating,
    )

    return PhoneNumberSyncResponse(
        id=phone_number.id,
        synced_at=now,
        phone_number=phone_number.phone_number,
        quality_rating=phone_number.quality_rating,
        message_limit=phone_number.message_limit,
        tier=phone_number.tier,
        status=phone_number.status,
    )


@router.post("/{phone_number_id}/exchange-token", response_model=PhoneNumberResponse)
async def exchange_token_for_long_term(
    phone_number_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Exchange short-lived access token for long-lived token.
    
    This endpoint attempts to exchange the current access token for a long-lived
    token (typically 60 days vs 1 hour). This is useful when you have a short-lived
    user access token and want to convert it to a long-lived one.
    
    Note: System user tokens are already long-lived and don't need exchange.
    
    Requires workspace admin access.
    """
    # Fetch phone number
    result = await session.execute(
        select(PhoneNumber).where(
            PhoneNumber.id == phone_number_id,
            PhoneNumber.deleted_at.is_(None),
        )
    )
    phone_number = result.scalar_one_or_none()

    if not phone_number:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Phone number not found."},
        )

    # Verify admin access
    await require_workspace_admin(phone_number.workspace_id, current_user, session)

    # Exchange token
    wa_client = WhatsAppClient(access_token=phone_number.access_token)
    long_lived_token, error = await wa_client.exchange_token_for_long_term()

    if not long_lived_token:
        log_event(
            "token_exchange_failed",
            level="warning",
            phone_number_id=str(phone_number_id),
            error_code=error.code if error else "unknown",
        )
        raise HTTPException(
            status_code=400,
            detail={
                "code": "TOKEN_EXCHANGE_FAILED",
                "message": error.message if error else "Failed to exchange token for long-lived token.",
            },
        )

    # Update phone number with new long-lived token
    phone_number.access_token = long_lived_token
    await session.commit()
    await session.refresh(phone_number)

    log_event(
        "token_exchanged",
        level="info",
        phone_number_id=str(phone_number_id),
    )

    return _phone_number_to_response(phone_number)
