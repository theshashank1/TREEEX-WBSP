"""
Webhook Worker - server/workers/webhook.py

Async worker that processes webhook events from Redis queue.
Handles: Messages, Statuses, Errors, Template Updates

ARCHITECTURE:
    - Pulls events from Redis queues (INBOUND_WEBHOOKS, MESSAGE_STATUS, HIGH_PRIORITY)
    - Processes each event type with dedicated handlers
    - Writes to PostgreSQL via SQLAlchemy async
    - Publishes real-time updates via Redis pub/sub
    - Moves failed jobs to Dead Letter Queue

RUNNING:
    python -m server.workers.webhook

    Or with multiple workers:
    python -m server.workers.webhook --workers 4
"""

from __future__ import annotations

import argparse
import asyncio
import signal
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.config import settings
from server.core.db import async_session_maker as async_session
from server.core.db import engine
from server.core.monitoring import log_event, log_exception
from server.core.redis import (
    Queue,
    dequeue,
    enqueue,
    key_realtime,
    move_to_dlq,
    publish,
)
from server.core.redis import shutdown as redis_shutdown
from server.core.redis import startup as redis_startup
from server.models.audit import WebhookLog
from server.models.base import (
    ConversationStatus,
    ConversationType,
    MessageDirection,
    MessageStatus,
    utc_now,
)
from server.models.contacts import Contact, PhoneNumber
from server.models.messaging import Conversation, MediaFile, Message

# ============================================================================
# WORKER STATE
# ============================================================================


class WorkerState:
    running: bool = True

    @classmethod
    def shutdown(cls):
        cls.running = False
        log_event("worker_shutdown_signal")


# ============================================================================
# EVENT HANDLERS
# ============================================================================


async def handle_message_event(session: AsyncSession, event: Dict[str, Any]) -> bool:
    """Process incoming WhatsApp message."""
    try:
        phone_number_id_meta = event.get("phone_number_id")  # Meta's phone_number_id
        wa_message_id = event.get("wa_message_id")
        from_number = event.get("from")  # Customer's WhatsApp number
        message_data = event.get("message", {})
        contact_data = event.get("contact", {})
        metadata = event.get("metadata", {})
        timestamp = event.get("timestamp")

        if not all([phone_number_id_meta, wa_message_id, from_number]):
            log_event("webhook_message_missing_fields", level="warning", event=event)
            return False

        phone_number = await session.execute(
            select(PhoneNumber).where(
                PhoneNumber.phone_number_id == phone_number_id_meta
            )
        )
        phone_number = phone_number.scalar_one_or_none()

        if not phone_number:
            log_event(
                "webhook_phone_not_found",
                level="warning",
                phone_number_id=phone_number_id_meta,
            )
            return False

        workspace_id = phone_number.workspace_id

        contact = await _get_or_create_contact(
            session=session,
            workspace_id=workspace_id,
            wa_id=contact_data.get("wa_id") or from_number,
            phone_number=from_number,
            name=contact_data.get("name"),
        )

        conversation = await _get_or_create_conversation(
            session=session,
            workspace_id=workspace_id,
            contact_id=contact.id,
            phone_number_id=phone_number.id,
        )

        message_time = utc_now()
        if timestamp:
            try:
                message_time = datetime.fromtimestamp(
                    int(timestamp), tz=timezone.utc
                ).replace(tzinfo=None)
            except (ValueError, TypeError):
                pass

        media_id = None
        message_type = message_data.get("type", "text")

        if message_type in ("image", "video", "audio", "document", "sticker"):
            media_id = await _create_media_placeholder(
                session=session,
                workspace_id=workspace_id,
                message_data=message_data,
                message_type=message_type,
            )

        content = _extract_message_content(message_data)

        message = Message(
            workspace_id=workspace_id,
            conversation_id=conversation.id,
            phone_number_id=phone_number.id,
            wa_message_id=wa_message_id,
            direction=MessageDirection.INCOMING.value,
            from_number=from_number,
            to_number=metadata.get("display_phone_number", phone_number.phone_number),
            type=message_type,
            content=content,
            media_id=media_id,
            status=MessageStatus.DELIVERED.value,  # Incoming messages are already delivered
            is_bot=False,
            created_at=message_time,
        )
        session.add(message)

        conversation.last_message_at = message_time
        conversation.last_inbound_at = message_time
        conversation.window_expires_at = message_time + timedelta(hours=24)
        conversation.unread_count += 1
        conversation.status = ConversationStatus.OPEN.value
        conversation.conversation_type = ConversationType.USER_INITIATED.value

        webhook_log = WebhookLog(
            workspace_id=workspace_id,
            phone_number_id=phone_number.id,
            event_type="message",
            event_id_hash=wa_message_id,
            payload=event,
            processed=True,
            processed_at=utc_now(),
        )
        session.add(webhook_log)

        await session.commit()

        if media_id and message_type in ("image", "video", "audio", "document"):
            await enqueue(
                Queue.MEDIA_DOWNLOAD,
                {
                    "media_id": str(media_id),
                    "workspace_id": str(workspace_id),
                    "wa_media_id": message_data.get(message_type, {}).get("id"),
                    "mime_type": message_data.get(message_type, {}).get("mime_type"),
                    "phone_number_id": phone_number_id_meta,
                },
            )

        await publish(
            key_realtime(str(workspace_id), "messages"),
            {
                "type": "new_message",
                "conversation_id": str(conversation.id),
                "message": message.to_dict(),
            },
        )

        log_event(
            "webhook_message_processed",
            wa_message_id=wa_message_id,
            conversation_id=str(conversation.id),
            message_type=message_type,
        )

        return True

    except Exception as e:
        log_exception("webhook_message_handler_error", e, event=event)
        await session.rollback()
        return False


async def handle_status_event(session: AsyncSession, event: Dict[str, Any]) -> bool:
    """Process message status update (sent/delivered/read/failed)."""
    try:
        wa_message_id = event.get("wa_message_id")
        status = event.get("status")
        timestamp = event.get("timestamp")
        phone_number_id_meta = event.get("phone_number_id")
        errors = event.get("errors")

        if not all([wa_message_id, status]):
            log_event("webhook_status_missing_fields", level="warning", event=event)
            return False

        result = await session.execute(
            select(Message).where(Message.wa_message_id == wa_message_id)
        )
        message = result.scalar_one_or_none()

        if not message:
            log_event(
                "webhook_status_message_not_found",
                level="debug",
                wa_message_id=wa_message_id,
                status=status,
            )
            return True

        status_time = utc_now()
        if timestamp:
            try:
                status_time = datetime.fromtimestamp(
                    int(timestamp), tz=timezone.utc
                ).replace(tzinfo=None)
            except (ValueError, TypeError):
                pass

        status_map = {
            "sent": MessageStatus.SENT.value,
            "delivered": MessageStatus.DELIVERED.value,
            "read": MessageStatus.READ.value,
            "failed": MessageStatus.FAILED.value,
        }

        new_status = status_map.get(status)
        if new_status:
            status_order = ["pending", "sent", "delivered", "read", "failed"]
            current_idx = (
                status_order.index(message.status)
                if message.status in status_order
                else -1
            )
            new_idx = (
                status_order.index(new_status) if new_status in status_order else -1
            )

            if new_status == MessageStatus.FAILED.value or new_idx > current_idx:
                message.status = new_status

        if status == "delivered" and not message.delivered_at:
            message.delivered_at = status_time
        elif status == "read" and not message.read_at:
            message.read_at = status_time
            if not message.delivered_at:
                message.delivered_at = status_time

        if status == "failed" and errors:
            error = errors[0] if isinstance(errors, list) else errors
            message.error_code = str(error.get("code", ""))
            message.error_message = error.get("message") or error.get("title")

        phone_number = await session.execute(
            select(PhoneNumber).where(
                PhoneNumber.phone_number_id == phone_number_id_meta
            )
        )
        phone_number = phone_number.scalar_one_or_none()

        webhook_log = WebhookLog(
            workspace_id=message.workspace_id,
            phone_number_id=phone_number.id if phone_number else None,
            event_type=f"status:{status}",
            event_id_hash=f"{wa_message_id}:{status}",
            payload=event,
            processed=True,
            processed_at=utc_now(),
        )
        session.add(webhook_log)

        await session.commit()

        await publish(
            key_realtime(str(message.workspace_id), "status"),
            {
                "type": "status_update",
                "message_id": str(message.id),
                "wa_message_id": wa_message_id,
                "status": new_status or status,
                "timestamp": status_time.isoformat(),
            },
        )

        log_event(
            "webhook_status_processed",
            wa_message_id=wa_message_id,
            status=status,
        )

        return True

    except Exception as e:
        log_exception("webhook_status_handler_error", e, event=event)
        await session.rollback()
        return False


async def handle_error_event(session: AsyncSession, event: Dict[str, Any]) -> bool:
    """Process error event from Meta."""
    try:
        error_code = event.get("code")
        error_title = event.get("title")
        error_message = event.get("message")
        phone_number_id_meta = event.get("phone_number_id")
        waba_id = event.get("waba_id")

        log_event(
            "webhook_error_received",
            level="error",
            error_code=error_code,
            error_title=error_title,
            error_message=error_message,
            phone_number_id=phone_number_id_meta,
        )

        phone_number = await session.execute(
            select(PhoneNumber).where(
                PhoneNumber.phone_number_id == phone_number_id_meta
            )
        )
        phone_number = phone_number.scalar_one_or_none()

        if phone_number:
            webhook_log = WebhookLog(
                workspace_id=phone_number.workspace_id,
                phone_number_id=phone_number.id,
                event_type="error",
                payload=event,
                processed=True,
                error=f"{error_code}: {error_title} - {error_message}",
                processed_at=utc_now(),
            )
            session.add(webhook_log)
            await session.commit()

        return True

    except Exception as e:
        log_exception("webhook_error_handler_error", e, event=event)
        await session.rollback()
        return False


async def handle_template_event(session: AsyncSession, event: Dict[str, Any]) -> bool:
    """Process template status update from Meta."""
    try:
        from server.models.marketing import Template

        template_name = event.get("message_template_name")
        template_id = event.get("message_template_id")
        template_event = event.get("event")  # APPROVED, REJECTED, etc.
        reason = event.get("reason")
        waba_id = event.get("waba_id")

        log_event(
            "webhook_template_received",
            template_name=template_name,
            template_id=template_id,
            event=template_event,
            reason=reason,
        )

        if template_id:
            result = await session.execute(
                select(Template).where(Template.meta_template_id == template_id)
            )
        else:
            result = await session.execute(
                select(Template).where(Template.name == template_name)
            )

        template = result.scalar_one_or_none()

        if template:
            status_map = {
                "APPROVED": "APPROVED",
                "REJECTED": "REJECTED",
                "DISABLED": "DISABLED",
                "PENDING_DELETION": "DISABLED",
                "FLAGGED": "REJECTED",
            }

            if template_event in status_map:
                template.status = status_map[template_event]

            if reason:
                template.rejection_reason = reason

            if template_id and not template.meta_template_id:
                template.meta_template_id = template_id

            webhook_log = WebhookLog(
                workspace_id=template.workspace_id,
                phone_number_id=template.phone_number_id,
                event_type=f"template:{template_event}",
                payload=event,
                processed=True,
                processed_at=utc_now(),
            )
            session.add(webhook_log)

            await session.commit()

            log_event(
                "webhook_template_processed",
                template_name=template_name,
                new_status=template.status,
            )

        return True

    except Exception as e:
        log_exception("webhook_template_handler_error", e, event=event)
        await session.rollback()
        return False


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


async def _get_or_create_contact(
    session: AsyncSession,
    workspace_id: UUID,
    wa_id: str,
    phone_number: str,
    name: Optional[str] = None,
) -> Contact:
    """Find existing contact or create new one."""

    result = await session.execute(
        select(Contact).where(
            and_(
                Contact.workspace_id == workspace_id,
                Contact.wa_id == wa_id,
            )
        )
    )
    contact = result.scalar_one_or_none()

    if contact:
        if name and name != contact.name:
            contact.name = name
        return contact

    contact = Contact(
        workspace_id=workspace_id,
        wa_id=wa_id,
        phone_number=phone_number,
        name=name,
        opted_in=True,  # Implicit opt-in when they message us
        opt_in_source="chat",
        opt_in_date=utc_now(),
    )
    session.add(contact)
    await session.flush()

    log_event("contact_created", workspace_id=str(workspace_id), wa_id=wa_id)

    return contact


async def _get_or_create_conversation(
    session: AsyncSession,
    workspace_id: UUID,
    contact_id: UUID,
    phone_number_id: UUID,
) -> Conversation:
    """Find existing conversation or create new one."""

    result = await session.execute(
        select(Conversation).where(
            and_(
                Conversation.workspace_id == workspace_id,
                Conversation.contact_id == contact_id,
                Conversation.phone_number_id == phone_number_id,
            )
        )
    )
    conversation = result.scalar_one_or_none()

    if conversation:
        return conversation

    now = utc_now()
    conversation = Conversation(
        workspace_id=workspace_id,
        contact_id=contact_id,
        phone_number_id=phone_number_id,
        status=ConversationStatus.OPEN.value,
        conversation_type=ConversationType.USER_INITIATED.value,
        last_message_at=now,
        last_inbound_at=now,
        window_expires_at=now + timedelta(hours=24),
        unread_count=0,
    )
    session.add(conversation)
    await session.flush()

    log_event(
        "conversation_created",
        workspace_id=str(workspace_id),
        contact_id=str(contact_id),
    )

    return conversation


async def _create_media_placeholder(
    session: AsyncSession,
    workspace_id: UUID,
    message_data: Dict[str, Any],
    message_type: str,
) -> Optional[UUID]:
    """Create a MediaFile placeholder for async download."""

    media_info = message_data.get(message_type, {})

    media = MediaFile(
        workspace_id=workspace_id,
        type=message_type,
        mime_type=media_info.get("mime_type"),
        file_name=media_info.get("filename"),
        # original_url will be fetched by media worker
    )
    session.add(media)
    await session.flush()

    return media.id


def _extract_message_content(message_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and normalize message content for storage."""

    message_type = message_data.get("type", "text")
    content: Dict[str, Any] = {"type": message_type}

    if message_type == "text":
        content["text"] = message_data.get("text", {}).get("body", "")

    elif message_type == "image":
        img = message_data.get("image", {})
        content["media_id"] = img.get("id")
        content["caption"] = img.get("caption")
        content["mime_type"] = img.get("mime_type")

    elif message_type == "video":
        vid = message_data.get("video", {})
        content["media_id"] = vid.get("id")
        content["caption"] = vid.get("caption")
        content["mime_type"] = vid.get("mime_type")

    elif message_type == "audio":
        aud = message_data.get("audio", {})
        content["media_id"] = aud.get("id")
        content["voice"] = aud.get("voice", False)
        content["mime_type"] = aud.get("mime_type")

    elif message_type == "document":
        doc = message_data.get("document", {})
        content["media_id"] = doc.get("id")
        content["filename"] = doc.get("filename")
        content["caption"] = doc.get("caption")
        content["mime_type"] = doc.get("mime_type")

    elif message_type == "sticker":
        sticker = message_data.get("sticker", {})
        content["media_id"] = sticker.get("id")
        content["animated"] = sticker.get("animated", False)
        content["mime_type"] = sticker.get("mime_type")

    elif message_type == "location":
        loc = message_data.get("location", {})
        content["latitude"] = loc.get("latitude")
        content["longitude"] = loc.get("longitude")
        content["name"] = loc.get("name")
        content["address"] = loc.get("address")

    elif message_type == "contacts":
        content["contacts"] = message_data.get("contacts", [])

    elif message_type == "interactive":
        interactive = message_data.get("interactive", {})
        interactive_type = interactive.get("type")
        content["interactive_type"] = interactive_type

        if interactive_type == "button_reply":
            reply = interactive.get("button_reply", {})
            content["button_id"] = reply.get("id")
            content["button_title"] = reply.get("title")

        elif interactive_type == "list_reply":
            reply = interactive.get("list_reply", {})
            content["list_id"] = reply.get("id")
            content["list_title"] = reply.get("title")
            content["list_description"] = reply.get("description")

    elif message_type == "button":
        button = message_data.get("button", {})
        content["text"] = button.get("text")
        content["payload"] = button.get("payload")

    elif message_type == "reaction":
        reaction = message_data.get("reaction", {})
        content["message_id"] = reaction.get("message_id")
        content["emoji"] = reaction.get("emoji")

    context = message_data.get("context")
    if context:
        content["context"] = {
            "message_id": context.get("id"),
            "from": context.get("from"),
        }

    return content


# ============================================================================
# WORKER LOOP
# ============================================================================


async def process_event(event: Dict[str, Any]) -> bool:
    """Process a single event from the queue."""
    event_type = event.get("type")

    handlers: Dict[str, Callable] = {
        "message": handle_message_event,
        "status": handle_status_event,
        "error": handle_error_event,
        "template_status": handle_template_event,
    }

    handler = handlers.get(event_type)

    if not handler:
        log_event("webhook_unknown_event_type", level="warning", event_type=event_type)
        return True  # Don't retry unknown types

    async with async_session() as session:
        return await handler(session, event)


async def worker_loop(worker_id: int = 0) -> None:
    """Main worker loop."""
    log_event("worker_started", worker_id=worker_id)

    queues = [
        Queue.HIGH_PRIORITY,
        Queue.INBOUND_WEBHOOKS,
        Queue.MESSAGE_STATUS,
        Queue.TEMPLATE_SYNC,
    ]

    retry_counts: Dict[str, int] = {}
    max_retries = 3

    while WorkerState.running:
        event = None
        source_queue = None

        try:
            for queue in queues:
                event = await dequeue(queue, timeout=1)
                if event:
                    source_queue = queue
                    break

            if not event:
                await asyncio.sleep(0.1)
                continue

            event_id = (
                event.get("wa_message_id") or event.get("message_id") or "unknown"
            )

            success = await process_event(event)

            if not success:
                retry_key = f"{source_queue.value}:{event_id}"
                retry_counts[retry_key] = retry_counts.get(retry_key, 0) + 1

                if retry_counts[retry_key] < max_retries:
                    log_event(
                        "worker_event_retry",
                        level="warning",
                        event_id=event_id,
                        attempt=retry_counts[retry_key],
                    )
                    await enqueue(source_queue, event)
                    await asyncio.sleep(1)
                else:
                    await move_to_dlq(
                        source_queue,
                        event,
                        f"Max retries exceeded ({max_retries})",
                    )
                    if retry_key in retry_counts:
                        del retry_counts[retry_key]
            else:
                retry_key = f"{source_queue.value}:{event_id}"
                if retry_key in retry_counts:
                    del retry_counts[retry_key]

        except Exception as e:
            log_exception("worker_loop_error", e)
            await asyncio.sleep(1)

    await redis_shutdown()
    log_event("worker_stopped", worker_id=worker_id)


async def run_workers(num_workers: int = 1) -> None:
    """Run multiple worker instances concurrently."""

    await redis_startup()

    log_event("workers_starting", num_workers=num_workers)

    workers = [
        asyncio.create_task(worker_loop(worker_id=i)) for i in range(num_workers)
    ]

    try:
        await asyncio.gather(*workers)
    except asyncio.CancelledError:
        log_event("workers_cancelled")
    finally:
        await redis_shutdown()
        await engine.dispose()
        log_event("workers_cleanup_complete")


# ============================================================================
# ENTRY POINT
# ============================================================================


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Webhook Worker")
    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=1,
        help="Number of worker instances (default: 1)",
    )
    args = parser.parse_args()

    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        log_event("shutdown_signal_received", signal=sig)
        WorkerState.shutdown()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run
    try:
        asyncio.run(run_workers(num_workers=args.workers))
    except KeyboardInterrupt:
        log_event("keyboard_interrupt")

    log_event("worker_exit")
    sys.exit(0)


if __name__ == "__main__":
    main()
