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
from server.models.contacts import Contact, PhoneNumber
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

    @classmethod
    def shutdown(cls):
        cls.running = False
        log_event("outbound_worker_shutdown_signal")

    @classmethod
    def pause(cls):
        cls.paused = True
        log_event("outbound_worker_paused")

    @classmethod
    def resume(cls):
        cls.paused = False
        log_event("outbound_worker_resumed")

    @property
    def avg_latency_ms(self) -> float:
        total = self.messages_sent + self.messages_failed
        if total == 0:
            return 0
        return self.total_latency_ms / total


# Global worker state
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


async def get_phone_credentials(
    session: AsyncSession,
    phone_number_id_meta: str,
    workspace_id: str,
) -> Optional[PhoneNumber]:
    result = await session.execute(
        select(PhoneNumber).where(
            PhoneNumber.phone_number_id == phone_number_id_meta,
            PhoneNumber.workspace_id == UUID(workspace_id),
            PhoneNumber.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def create_or_update_message(
    session: AsyncSession,
    msg: OutboundMessage,
    phone_number: PhoneNumber,
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
        conversation = await get_or_create_conversation(session, msg, phone_number)
        content = build_message_content(msg)

        message = Message(
            id=UUID(msg.message_id),
            workspace_id=UUID(msg.workspace_id),
            conversation_id=conversation.id,
            phone_number_id=phone_number.id,
            wa_message_id=wa_message_id,
            direction=MessageDirection.OUTGOING.value,
            from_number=phone_number.phone_number,
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
    phone_number: PhoneNumber,
) -> Conversation:
    contact = await get_or_create_contact(session, msg, phone_number)

    result = await session.execute(
        select(Conversation).where(
            Conversation.workspace_id == UUID(msg.workspace_id),
            Conversation.contact_id == contact.id,
            Conversation.phone_number_id == phone_number.id,
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
        phone_number_id=phone_number.id,
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
    phone_number: PhoneNumber,
) -> Contact:
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

    contact = Contact(
        workspace_id=UUID(msg.workspace_id),
        wa_id=wa_id,
        phone_number=msg.to_number,
        opted_in=False,
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
    if isinstance(msg, TextMessage):
        return await client.send_text_message(
            to_number=msg.to_number,
            text=msg.text,
            preview_url=msg.preview_url,
            reply_to_message_id=msg.reply_to_message_id,
        )

    if isinstance(msg, TemplateMessage):
        components = None
        if msg.components:
            components = [c.model_dump() for c in msg.components]
        return await client.send_template_message(
            to_number=msg.to_number,
            template_name=msg.template_name,
            language_code=msg.language_code,
            components=components,
        )

    if isinstance(msg, MediaMessage):
        return await client.send_media_message(
            to_number=msg.to_number,
            media_type=msg.media_type,
            media_url=msg.media_url,
            media_id=msg.media_id,
            caption=msg.caption,
            filename=msg.filename,
            reply_to_message_id=msg.reply_to_message_id,
        )

    if isinstance(msg, InteractiveButtonsMessage):
        return await client.send_interactive_buttons(
            to_number=msg.to_number,
            body_text=msg.body_text,
            buttons=[{"id": b.id, "title": b.title} for b in msg.buttons],
            header_text=msg.header_text,
            footer_text=msg.footer_text,
            reply_to_message_id=msg.reply_to_message_id,
        )

    if isinstance(msg, InteractiveListMessage):
        sections = []
        for section in msg.sections:
            sections.append(
                {
                    "title": section.title,
                    "rows": [
                        {"id": r.id, "title": r.title, "description": r.description}
                        for r in section.rows
                    ],
                }
            )
        return await client.send_interactive_list(
            to_number=msg.to_number,
            body_text=msg.body_text,
            button_text=msg.button_text,
            sections=sections,
            header_text=msg.header_text,
            footer_text=msg.footer_text,
            reply_to_message_id=msg.reply_to_message_id,
        )

    if isinstance(msg, LocationMessage):
        return await client.send_location(
            to_number=msg.to_number,
            latitude=msg.latitude,
            longitude=msg.longitude,
            name=msg.name,
            address=msg.address,
            reply_to_message_id=msg.reply_to_message_id,
        )

    if isinstance(msg, ReactionMessage):
        return await client.send_reaction(
            to_number=msg.to_number,
            message_id=msg.target_message_id,
            emoji=msg.emoji,
        )

    if isinstance(msg, MarkAsReadMessage):
        return await client.mark_as_read(msg.target_message_id)

    return SendResult(
        error={"code": -1, "message": f"Unknown message type: {msg.type}"}
    )


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
            phone_number = await get_phone_credentials(
                session, msg.phone_number_id, msg.workspace_id
            )

            if not phone_number:
                log_event(
                    "outbound_phone_not_found",
                    level="error",
                    message_id=message_id,
                    phone_number_id=msg.phone_number_id,
                )
                await move_to_dlq(
                    Queue.OUTBOUND_MESSAGES,
                    data,
                    f"Phone number not found: {msg.phone_number_id}",
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

            await create_or_update_message(
                session,
                msg,
                phone_number,
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
                access_token=phone_number.access_token,
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
            await session.commit()

            worker_state.total_latency_ms += (time.monotonic() - start_time) * 1000
            return True

    except Exception as e:
        log_exception("outbound_worker_error", e, message_id=message_id)
        return False


async def worker_loop(worker_id: int = 0) -> None:
    """Main worker loop handling Redis queue."""
    log_event("outbound_worker_started", worker_id=worker_id)
    config = WorkerConfig()

    await redis_startup()
    rate_limiter = TokenBucketRateLimiter(
        rate=config.rate_limit_per_phone,
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
        await asyncio.gather(*tasks, return_exceptions=True)

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
