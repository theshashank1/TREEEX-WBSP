"""
Outbound Worker - server/workers/outbound.py

Production-ready async worker that processes outbound WhatsApp messages from Redis queue.
Handles all message types with idempotency, rate limiting, retries, and DB transactions.

ARCHITECTURE:
    - Pulls messages from Redis queue (OUTBOUND_MESSAGES)
    - Validates message schema
"""

from __future__ import annotations

import argparse
import asyncio
import random
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from server.core.config import settings
from server.core.db import async_session_maker as async_session
from server.core.monitoring import log_event, log_exception
from server.core.rate_limiter import TokenBucketRateLimiter
from server.core.redis import (
    TTL,
    Queue,
    cache_get,
    cache_set,
    dequeue,
    enqueue,
    get_redis,
    is_duplicate,
    move_to_dlq,
)
from server.core.redis import shutdown as redis_shutdown
from server.core.redis import startup as redis_startup
from server.models.base import (
    ConversationStatus,
    ConversationType,
    MessageDirection,
    MessageStatus,
    utc_now,
)
from server.models.contacts import Channel, Contact
from server.models.messaging import Conversation, MediaFile, Message
from server.schemas.outbound import (
    InteractiveButtonsMessage,
    InteractiveListMessage,
    LocationMessage,
    MarkAsReadMessage,
    MediaMessage,
    OutboundMessage,
    ReactionMessage,
    TemplateMessage,
    TextMessage,
    parse_outbound_message,
)
from server.services.azure_storage import extract_blob_name_from_url, generate_sas_url
from server.whatsapp.outbound import OutboundClient, SendResult
from server.whatsapp.renderer import render

# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass
class WorkerConfig:
    rate_limit_per_phone: float = 80
    rate_limit_global: float = 500

    max_retries: int = 5
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter_factor: float = 0.5

    queue_timeout: int = 5
    batch_size: int = 10

    idempotency_ttl: int = TTL.IDEMPOTENCY


# =============================================================================
# WORKER STATE
# =============================================================================


@dataclass
class WorkerState:
    running: bool = True
    paused: bool = False

    messages_sent: int = 0
    messages_failed: int = 0
    messages_retried: int = 0
    total_latency_ms: float = 0

    def shutdown(self):
        self.running = False
        log_event("outbound_worker_shutdown_signal")

    def pause(self):
        self.paused = True
        log_event("outbound_worker_paused")

    def resume(self):
        self.paused = False
        log_event("outbound_worker_resumed")

    @property
    def avg_latency_ms(self) -> float:
        total = self.messages_sent + self.messages_failed
        if total == 0:
            return 0
        return self.total_latency_ms / total


# Global worker state instance
worker_state = WorkerState()


# =============================================================================
# RETRY LOGIC
# =============================================================================


def calculate_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter_factor: float = 0.5,
) -> float:
    """Calculate exponential backoff with jitter."""
    delay = base_delay * (2 ** (attempt - 1))
    delay = min(delay, max_delay)

    jitter = delay * jitter_factor
    delay = delay + random.uniform(-jitter, jitter)

    return max(0.1, delay)


# =============================================================================
# IDEMPOTENCY
# =============================================================================


def idempotency_key(message_id: str) -> str:
    return f"outbound:sent:{message_id}"


async def check_already_sent(message_id: str) -> bool:
    key = idempotency_key(message_id)
    result = await cache_get(key, deserialize=False)
    return result is not None


async def mark_as_sent(message_id: str, wa_message_id: str) -> None:
    key = idempotency_key(message_id)
    await cache_set(key, wa_message_id, ttl=TTL.IDEMPOTENCY, serialize=False)


# =============================================================================
# MEDIA RESOLUTION
# =============================================================================


def is_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except (ValueError, TypeError):
        return False


async def resolve_media_source(
    session: AsyncSession,
    media_id: Optional[str],
    media_url: Optional[str],
    workspace_id: str,
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Resolve media source for WhatsApp API.
    If media_id is an internal UUID, generate a SAS URL.
    """
    if media_url:
        log_event(
            "media_resolved",
            level="debug",
            source="direct_url",
            has_url=True,
        )
        return (media_url, None, None)

    if not media_id:
        return (None, None, "No media source provided (need media_url or media_id)")

    if is_uuid(media_id):
        media_file = await session.get(MediaFile, UUID(media_id))

        if not media_file:
            log_event("media_not_found", level="warning", media_id=media_id)
            return (None, None, f"Media file not found: {media_id}")

        if str(media_file.workspace_id) != workspace_id:
            log_event(
                "media_workspace_mismatch",
                level="warning",
                media_id=media_id,
                expected_workspace=workspace_id,
            )
            return (None, None, "Media file belongs to different workspace")

        if not media_file.storage_url:
            return (None, None, "Media file has no storage URL (not uploaded yet)")

        blob_name = extract_blob_name_from_url(media_file.storage_url)
        if not blob_name:
            log_event(
                "media_url_parse_failed",
                level="error",
                media_id=media_id,
                storage_url=media_file.storage_url[:50] + "...",
            )
            return (None, None, "Failed to parse storage URL for SAS generation")

        sas_url = generate_sas_url(blob_name, expiry_minutes=60)
        if not sas_url:
            return (None, None, "Failed to generate SAS URL for media access")

        log_event(
            "media_resolved",
            level="info",
            source="database",
            media_id=media_id,
            media_type=media_file.type,
        )
        return (sas_url, None, None)

    log_event(
        "media_resolved",
        level="debug",
        source="meta_id",
        media_id=media_id[:8] + "..." if len(media_id) > 8 else media_id,
    )
    return (None, media_id, None)


# =============================================================================
# MESSAGE PROCESSING
# =============================================================================


async def get_channel_credentials(
    session: AsyncSession,
    meta_phone_number_id: str,
    workspace_id: str,
) -> Optional[Channel]:
    result = await session.execute(
        select(Channel).where(
            Channel.meta_phone_number_id == meta_phone_number_id,
            Channel.workspace_id == UUID(workspace_id),
            Channel.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def create_or_update_message(
    session: AsyncSession,
    msg: OutboundMessage,
    channel: Channel,
    status: str,
    wa_message_id: Optional[str] = None,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
) -> Message:
    """Create or update message record in database."""
    result = await session.execute(
        select(Message).where(
            Message.workspace_id == UUID(msg.workspace_id),
            Message.id == UUID(msg.message_id),
        )
    )
    message = result.scalar_one_or_none()

    if message:
        message.status = status
        if wa_message_id:
            message.wa_message_id = wa_message_id
        if error_code:
            message.error_code = error_code
        if error_message:
            message.error_message = error_message
    else:
        conversation = await get_or_create_conversation(session, msg, channel)
        content = build_message_content(msg)

        message = Message(
            id=UUID(msg.message_id),
            workspace_id=UUID(msg.workspace_id),
            conversation_id=conversation.id,
            channel_id=channel.id,
            wa_message_id=wa_message_id,
            direction=MessageDirection.OUTGOING.value,
            from_number=channel.phone_number,
            to_number=msg.to_number,
            type=get_message_type_for_db(msg),
            content=content,
            status=status,
            error_code=error_code,
            error_message=error_message,
            is_bot=msg.sent_by is None,
            sent_by=UUID(msg.sent_by) if msg.sent_by else None,
        )
        session.add(message)

    return message


async def get_or_create_conversation(
    session: AsyncSession,
    msg: OutboundMessage,
    channel: Channel,
) -> Conversation:
    contact = await get_or_create_contact(session, msg, channel)

    result = await session.execute(
        select(Conversation).where(
            Conversation.workspace_id == UUID(msg.workspace_id),
            Conversation.contact_id == contact.id,
            Conversation.channel_id == channel.id,
        )
    )
    conversation = result.scalar_one_or_none()

    if conversation:
        conversation.last_message_at = utc_now()
        return conversation

    now = utc_now()
    conversation = Conversation(
        workspace_id=UUID(msg.workspace_id),
        contact_id=contact.id,
        channel_id=channel.id,
        status=ConversationStatus.OPEN.value,
        conversation_type=ConversationType.BUSINESS_INITIATED.value,
        last_message_at=now,
        unread_count=0,
    )
    session.add(conversation)
    await session.flush()

    return conversation


async def get_or_create_contact(
    session: AsyncSession,
    msg: OutboundMessage,
    channel: Channel,
) -> Contact:
    """Get or create contact identity (workspace-level)."""
    wa_id = msg.to_number.lstrip("+")

    result = await session.execute(
        select(Contact).where(
            Contact.workspace_id == UUID(msg.workspace_id),
            Contact.wa_id == wa_id,
            Contact.deleted_at.is_(None),
        )
    )
    contact = result.scalar_one_or_none()

    if contact:
        return contact

    # Create contact identity only - no opt-in status (managed per phone)
    contact = Contact(
        workspace_id=UUID(msg.workspace_id),
        wa_id=wa_id,
        phone_number=msg.to_number,
        source_channel_id=channel.id,  # First channel to contact = source
    )
    session.add(contact)
    await session.flush()

    log_event(
        "contact_created_outbound",
        workspace_id=msg.workspace_id,
    )

    return contact


def get_message_type_for_db(msg: OutboundMessage) -> str:
    type_map = {
        "text_message": "text",
        "template_message": "template",
        "media_message": "image",
        "interactive_buttons": "interactive",
        "interactive_list": "interactive",
        "location_message": "location",
        "reaction_message": "reaction",
        "mark_as_read": "status",
    }

    if isinstance(msg, MediaMessage):
        return msg.media_type

    return type_map.get(msg.type, "unknown")


def build_message_content(msg: OutboundMessage) -> Dict[str, Any]:
    if isinstance(msg, TextMessage):
        return {"type": "text", "text": msg.text, "preview_url": msg.preview_url}

    if isinstance(msg, TemplateMessage):
        return {
            "type": "template",
            "template_name": msg.template_name,
            "language": msg.language_code,
            "components": (
                [c.model_dump() for c in msg.components] if msg.components else None
            ),
        }

    if isinstance(msg, MediaMessage):
        return {
            "type": msg.media_type,
            "media_url": msg.media_url,
            "media_id": msg.media_id,
            "caption": msg.caption,
            "filename": msg.filename,
        }

    if isinstance(msg, InteractiveButtonsMessage):
        return {
            "type": "interactive",
            "interactive_type": "button",
            "body": msg.body_text,
            "buttons": [b.model_dump() for b in msg.buttons],
            "header": msg.header_text,
            "footer": msg.footer_text,
        }

    if isinstance(msg, InteractiveListMessage):
        return {
            "type": "interactive",
            "interactive_type": "list",
            "body": msg.body_text,
            "button": msg.button_text,
            "sections": [s.model_dump() for s in msg.sections],
            "header": msg.header_text,
            "footer": msg.footer_text,
        }

    if isinstance(msg, LocationMessage):
        return {
            "type": "location",
            "latitude": msg.latitude,
            "longitude": msg.longitude,
            "name": msg.name,
            "address": msg.address,
        }

    if isinstance(msg, ReactionMessage):
        return {
            "type": "reaction",
            "message_id": msg.target_message_id,
            "emoji": msg.emoji,
        }

    if isinstance(msg, MarkAsReadMessage):
        return {
            "type": "status",
            "status": "read",
            "message_id": msg.target_message_id,
        }

    return {"type": "unknown"}


async def send_message(
    client: OutboundClient,
    msg: OutboundMessage,
) -> SendResult:
    """
    Send any message type using Command → Renderer → Client flow.

    Simplified from 90+ lines to use the renderer module.
    """
    # Special case: mark as read has different flow
    if isinstance(msg, MarkAsReadMessage):
        return await client.mark_as_read(msg.target_message_id)

    # Standard flow: render command to dict, send via client
    try:
        payload = render(msg)
        return await client.send_payload(payload)
    except ValueError as e:
        return SendResult(error={"code": -1, "message": str(e)})


# =============================================================================
# MAIN PROCESSING
# =============================================================================


async def process_outbound_message(
    data: Dict[str, Any],
    config: WorkerConfig,
    rate_limiter: TokenBucketRateLimiter,
) -> bool:
    """
    Process a single outbound message from the queue.
    Returns True if processed successfully or permanently failed.
    Returns False if should be retried.
    """
    start_time = time.monotonic()
    message_id = data.get("message_id", "unknown")

    try:
        try:
            msg = parse_outbound_message(data)
        except (ValidationError, ValueError) as e:
            log_event(
                "outbound_validation_error",
                level="warning",
                message_id=message_id,
                error=str(e),
            )
            await move_to_dlq(Queue.OUTBOUND_MESSAGES, data, f"Validation error: {e}")
            worker_state.messages_failed += 1
            return True

        if await check_already_sent(msg.message_id):
            log_event(
                "outbound_duplicate_skipped",
                level="debug",
                message_id=msg.message_id,
            )
            return True

        async with async_session() as session:
            channel = await get_channel_credentials(
                session, msg.phone_number_id, msg.workspace_id
            )

            if not channel:
                log_event(
                    "outbound_channel_not_found",
                    level="error",
                    message_id=message_id,
                    phone_number_id=msg.phone_number_id,
                )
                await move_to_dlq(
                    Queue.OUTBOUND_MESSAGES,
                    data,
                    f"Channel not found: {msg.phone_number_id}",
                )
                worker_state.messages_failed += 1
                return True

            acquired = await rate_limiter.wait_for_token(
                msg.phone_number_id,
                timeout=30.0,
            )
            if not acquired:
                log_event(
                    "outbound_rate_limit_timeout",
                    level="warning",
                    message_id=message_id,
                )
                return False

            # Get or create contact identity
            contact = await get_or_create_contact(session, msg, channel)

            # Check per-channel opt-in permission
            from server.models.contacts import ContactChannelState

            state_result = await session.execute(
                select(ContactChannelState).where(
                    ContactChannelState.contact_id == contact.id,
                    ContactChannelState.channel_id == channel.id,
                )
            )
            channel_state = state_result.scalar_one_or_none()

            # Enforce opt-in (skip for template messages which can be used for initial outreach)
            if not isinstance(msg, TemplateMessage):
                if not channel_state or not channel_state.opt_in_status:
                    log_event(
                        "outbound_blocked_no_optin",
                        level="warning",
                        message_id=message_id,
                        contact_id=str(contact.id),
                        channel_id=str(channel.id),
                    )
                    await move_to_dlq(
                        Queue.OUTBOUND_MESSAGES,
                        data,
                        "Contact has not opted in for this channel",
                    )
                    worker_state.messages_failed += 1
                    return True

            # Check if blocked
            if channel_state and channel_state.blocked:
                log_event(
                    "outbound_blocked_by_contact",
                    level="warning",
                    message_id=message_id,
                )
                await move_to_dlq(
                    Queue.OUTBOUND_MESSAGES,
                    data,
                    "Contact has blocked this channel",
                )
                worker_state.messages_failed += 1
                return True

            await create_or_update_message(
                session,
                msg,
                channel,
                status=MessageStatus.PENDING.value,
            )
            await session.commit()

            resolved_media_url = None
            resolved_media_id = None
            if isinstance(msg, MediaMessage):
                resolved_media_url, resolved_media_id, media_error = (
                    await resolve_media_source(
                        session, msg.media_id, msg.media_url, msg.workspace_id
                    )
                )
                if media_error:
                    log_event(
                        "outbound_media_resolution_failed",
                        level="error",
                        message_id=message_id,
                        error=media_error,
                    )
                    await move_to_dlq(
                        Queue.OUTBOUND_MESSAGES,
                        data,
                        f"Media resolution failed: {media_error}",
                    )
                    worker_state.messages_failed += 1
                    return True

                if resolved_media_url:
                    msg.media_url = resolved_media_url
                if resolved_media_id:
                    msg.media_id = resolved_media_id

            client = OutboundClient(
                access_token=channel.access_token,
                phone_number_id=msg.phone_number_id,
            )

            result = await send_message(client, msg)

            if result.success:
                status = MessageStatus.SENT.value
                wa_message_id = result.message_id
                error_code = None
                error_message = None

                await mark_as_sent(msg.message_id, wa_message_id)
                worker_state.messages_sent += 1

                log_event(
                    "outbound_message_sent",
                    message_id=msg.message_id,
                    wa_message_id=wa_message_id,
                    type=msg.type,
                )
            else:
                status = MessageStatus.FAILED.value
                wa_message_id = None
                error_code = str(result.error.get("code") or "")
                error_message = result.error.get("message") or "Unknown error"

                worker_state.messages_failed += 1
                log_event(
                    "outbound_message_failed",
                    level="error",
                    message_id=msg.message_id,
                    error=error_message,
                )

            await create_or_update_message(
                session,
                msg,
                phone_number,
                status=status,
                wa_message_id=wa_message_id,
                error_code=error_code,
                error_message=error_message,
            )
            if data.get("is_campaign") and data.get("campaign_message_id"):
                await update_campaign_status(
                    session,
                    data["campaign_message_id"],
                    status,
                    wa_message_id,
                    error_message,
                )

            await session.commit()

            worker_state.total_latency_ms += (time.monotonic() - start_time) * 1000
            return True

    except Exception as e:
        log_exception("outbound_worker_error", e, message_id=message_id)
        return False


async def update_campaign_status(
    session: AsyncSession,
    campaign_message_id: str,
    status: str,
    wa_message_id: Optional[str] = None,
    error_message: Optional[str] = None,
):
    """
    Update campaign message status and increment campaign counters.
    Called after Meta API response to track sent/failed counts.
    """
    from datetime import datetime, timezone

    from server.models.marketing import Campaign, CampaignMessage

    result = await session.execute(
        select(CampaignMessage).where(CampaignMessage.id == UUID(campaign_message_id))
    )
    msg = result.scalar_one_or_none()

    if not msg:
        log_event("campaign_msg_not_found", id=campaign_message_id, level="warning")
        return

    # Update message fields
    msg.status = status
    if error_message:
        msg.error_message = error_message
    if status == MessageStatus.SENT.value:
        msg.sent_at = datetime.now(timezone.utc).replace(tzinfo=None)

    # Update campaign counters atomically
    if status == MessageStatus.SENT.value:
        await session.execute(
            update(Campaign)
            .where(Campaign.id == msg.campaign_id)
            .values(sent_count=Campaign.sent_count + 1)
        )
    elif status == MessageStatus.FAILED.value:
        await session.execute(
            update(Campaign)
            .where(Campaign.id == msg.campaign_id)
            .values(failed_count=Campaign.failed_count + 1)
        )


async def worker_loop(worker_id: int = 0) -> None:
    """Main worker loop handling Redis queue."""
    log_event("outbound_worker_started", worker_id=worker_id)
    config = WorkerConfig()

    await redis_startup()
    rate_limiter = TokenBucketRateLimiter(
        capacity=config.rate_limit_per_phone,
        refill_rate=config.rate_limit_per_phone,
        global_capacity=config.rate_limit_global,
        global_refill_rate=config.rate_limit_global,
    )

    retry_counts: Dict[str, int] = {}

    log_event("outbound_worker_started", worker_id=worker_id)

    while worker_state.running:
        # Check if paused
        while worker_state.paused and worker_state.running:
            await asyncio.sleep(1)

        if not worker_state.running:
            break

        try:
            # Dequeue message
            data = await dequeue(Queue.OUTBOUND_MESSAGES, timeout=config.queue_timeout)

            if not data:
                continue  # No messages, loop again

            message_id = data.get("message_id", "unknown")

            # Process message
            success = await process_outbound_message(data, config, rate_limiter)

            if not success:
                # Need to retry
                retry_key = message_id
                retry_counts[retry_key] = retry_counts.get(retry_key, 0) + 1
                attempt = retry_counts[retry_key]

                if attempt < config.max_retries:
                    # Calculate backoff
                    delay = calculate_backoff(
                        attempt,
                        config.base_delay,
                        config.max_delay,
                        config.jitter_factor,
                    )

                    log_event(
                        "outbound_retry_scheduled",
                        level="info",
                        message_id=message_id,
                        attempt=attempt,
                        delay_seconds=round(delay, 2),
                    )

                    # Wait then re-queue
                    await asyncio.sleep(delay)
                    await enqueue(Queue.OUTBOUND_MESSAGES, data)
                else:
                    # Max retries exceeded
                    log_event(
                        "outbound_max_retries",
                        level="error",
                        message_id=message_id,
                        attempts=attempt,
                    )
                    await move_to_dlq(
                        Queue.OUTBOUND_MESSAGES,
                        data,
                        f"Max retries ({config.max_retries}) exceeded",
                    )
                    worker_state.messages_failed += 1
                    del retry_counts[retry_key]
            else:
                # Success or permanent failure - clean up retry counter
                if message_id in retry_counts:
                    del retry_counts[message_id]

        except Exception as e:
            log_exception("outbound_worker_loop_error", e, worker_id=worker_id)
            await asyncio.sleep(1)  # Prevent tight loop on errors

    log_event(
        "outbound_worker_stopped",
        worker_id=worker_id,
        messages_sent=worker_state.messages_sent,
        messages_failed=worker_state.messages_failed,
        messages_retried=worker_state.messages_retried,
        avg_latency_ms=round(worker_state.avg_latency_ms, 2),
    )


# =============================================================================
# MAIN
# =============================================================================


async def main(num_workers: int = 1) -> None:
    """Main entry point for the outbound worker."""

    # Setup signal handlers
    def handle_signal(sig, frame):
        worker_state.running = False
        log_event("outbound_shutdown_received", signal=sig)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Initialize Redis
    await redis_startup()

    log_event(
        "outbound_workers_starting",
        num_workers=num_workers,
    )

    try:
        # Create worker tasks
        tasks = [
            asyncio.create_task(worker_loop(worker_id=i)) for i in range(num_workers)
        ]

        # Wait for all workers
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log any exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                log_exception(f"Worker {i} failed", result)

    finally:
        await redis_shutdown()
        log_event("outbound_workers_shutdown_complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WhatsApp Outbound Message Worker")
    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=1,
        help="Number of worker coroutines (default: 1)",
    )
    args = parser.parse_args()

    asyncio.run(main(num_workers=args.workers))
