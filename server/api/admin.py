"""
Admin API Endpoints - server/api/admin.py

Admin endpoints for managing the outbound messaging system.
Includes: requeue failed messages, inspect message state, worker health.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.db import get_async_session
from server.core.monitoring import log_event
from server.core.redis import Queue, enqueue, queue_length, redis_health
from server.models.base import MessageStatus
from server.models.messaging import Message

router = APIRouter(prefix="/admin", tags=["Admin"])


# =============================================================================
# SCHEMAS
# =============================================================================


class RequeueRequest(BaseModel):
    """Request to requeue failed messages."""

    message_ids: Optional[List[str]] = None  # If None, requeue all failed
    max_messages: int = 100


class RequeueResponse(BaseModel):
    """Response from requeue operation."""

    requeued_count: int
    message_ids: List[str]


class MessageStateResponse(BaseModel):
    """Message state information."""

    id: str
    workspace_id: str
    conversation_id: str
    wa_message_id: Optional[str]
    direction: str
    to_number: str
    type: str
    status: str
    error_code: Optional[str]
    error_message: Optional[str]
    created_at: str
    delivered_at: Optional[str]
    read_at: Optional[str]


class QueueStatsResponse(BaseModel):
    """Queue statistics."""

    outbound_pending: int
    dead_letter: int
    high_priority: int


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    redis: bool
    database: bool
    details: dict


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post("/messages/requeue", response_model=RequeueResponse)
async def requeue_failed_messages(
    request: RequeueRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Requeue failed messages for retry.

    If message_ids is provided, only requeues those specific messages.
    Otherwise, requeues up to max_messages failed messages.
    """
    try:
        if request.message_ids:
            # Requeue specific messages
            message_uuids = [UUID(mid) for mid in request.message_ids]
            result = await session.execute(
                select(Message).where(
                    Message.id.in_(message_uuids),
                    Message.status == MessageStatus.FAILED.value,
                )
            )
        else:
            # Requeue all failed (up to limit)
            result = await session.execute(
                select(Message)
                .where(Message.status == MessageStatus.FAILED.value)
                .order_by(Message.created_at.desc())
                .limit(request.max_messages)
            )

        messages = result.scalars().all()
        requeued_ids = []

        for msg in messages:
            # Build queue payload
            payload = {
                "type": _get_message_type(msg.type),
                "message_id": str(msg.id),
                "workspace_id": str(msg.workspace_id),
                "phone_number_id": str(msg.phone_number_id),
                "to_number": msg.to_number,
                **msg.content,  # Include original content
            }

            # Enqueue
            success = await enqueue(Queue.OUTBOUND_MESSAGES, payload)
            if success:
                requeued_ids.append(str(msg.id))
                # Reset status to pending
                msg.status = MessageStatus.PENDING.value
                msg.error_code = None
                msg.error_message = None

        await session.commit()

        log_event(
            "admin_messages_requeued",
            count=len(requeued_ids),
        )

        return RequeueResponse(
            requeued_count=len(requeued_ids),
            message_ids=requeued_ids,
        )

    except Exception as e:
        log_event("admin_requeue_error", level="error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/{message_id}", response_model=MessageStateResponse)
async def get_message_state(
    message_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get the current state of a message by ID.
    """
    try:
        result = await session.execute(
            select(Message).where(Message.id == UUID(message_id))
        )
        message = result.scalar_one_or_none()

        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        return MessageStateResponse(
            id=str(message.id),
            workspace_id=str(message.workspace_id),
            conversation_id=str(message.conversation_id),
            wa_message_id=message.wa_message_id,
            direction=message.direction,
            to_number=message.to_number,
            type=message.type,
            status=message.status,
            error_code=message.error_code,
            error_message=message.error_message,
            created_at=message.created_at.isoformat(),
            delivered_at=(
                message.delivered_at.isoformat() if message.delivered_at else None
            ),
            read_at=message.read_at.isoformat() if message.read_at else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        log_event("admin_get_message_error", level="error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queues/stats", response_model=QueueStatsResponse)
async def get_queue_stats():
    """
    Get current queue statistics.
    """
    try:
        outbound = await queue_length(Queue.OUTBOUND_MESSAGES)
        dlq = await queue_length(Queue.DEAD_LETTER)
        priority = await queue_length(Queue.HIGH_PRIORITY)

        return QueueStatsResponse(
            outbound_pending=outbound,
            dead_letter=dlq,
            high_priority=priority,
        )

    except Exception as e:
        log_event("admin_queue_stats_error", level="error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check(
    session: AsyncSession = Depends(get_async_session),
):
    """
    Check health of all system components.
    """
    redis_ok = await redis_health()

    # Check database
    db_ok = False
    try:
        await session.execute(select(func.now()))
        db_ok = True
    except Exception:
        pass

    # Get queue stats
    queue_stats = {}
    try:
        queue_stats = {
            "outbound_pending": await queue_length(Queue.OUTBOUND_MESSAGES),
            "dead_letter": await queue_length(Queue.DEAD_LETTER),
        }
    except Exception:
        pass

    overall_status = "healthy" if (redis_ok and db_ok) else "unhealthy"

    return HealthResponse(
        status=overall_status,
        redis=redis_ok,
        database=db_ok,
        details={
            "queues": queue_stats,
        },
    )


@router.get("/messages/stats")
async def get_message_stats(
    workspace_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get message statistics by status.
    """
    try:
        query = select(Message.status, func.count(Message.id).label("count")).group_by(
            Message.status
        )

        if workspace_id:
            query = query.where(Message.workspace_id == UUID(workspace_id))

        result = await session.execute(query)
        stats = {row.status: row.count for row in result}

        return {
            "total": sum(stats.values()),
            "by_status": stats,
        }

    except Exception as e:
        log_event("admin_message_stats_error", level="error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# HELPERS
# =============================================================================


def _get_message_type(db_type: str) -> str:
    """Map DB message type back to queue message type."""
    type_map = {
        "text": "text_message",
        "template": "template_message",
        "image": "media_message",
        "video": "media_message",
        "audio": "media_message",
        "document": "media_message",
        "sticker": "media_message",
        "interactive": "interactive_buttons",  # Default to buttons
        "location": "location_message",
        "reaction": "reaction_message",
    }
    return type_map.get(db_type, "text_message")
