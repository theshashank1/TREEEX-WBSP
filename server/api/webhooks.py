"""
Webhook Endpoint - processing Meta WhatsApp events.
"""

import hashlib
import hmac
import json
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request, Response

from server.core.config import settings
from server.core.monitoring import log_event, log_exception
from server.core.redis import Queue, enqueue, is_duplicate, key_idempotency
from server.schemas.webhooks import WebhookEventType

router = APIRouter(prefix="/webhook", tags=["Webhooks"])


@router.get("")
async def verify_webhook(request: Request):
    """
    Webhook Verification (Setup Only).
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == settings.META_WEBHOOK_VERIFY_TOKEN:
        log_event("webhook_verified", mode=mode)
        return Response(content=challenge, media_type="text/plain")

    log_event(
        "webhook_verification_failed",
        level="warning",
        mode=mode,
        token_match=token == settings.META_WEBHOOK_VERIFY_TOKEN,
    )
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
):
    """
    Receives ALL events from Meta.
    Verifies signature, checks idempotency, and queues events.
    Always returns 200 OK.
    """
    try:
        raw_body = await request.body()

        if not _verify_signature(raw_body, x_hub_signature_256):
            log_event("webhook_signature_invalid", level="warning")
            return {"status": "ok"}

        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError as e:
            log_event("webhook_json_invalid", level="error", error=str(e))
            return {"status": "ok"}

        if not _is_valid_payload(payload):
            log_event("webhook_payload_invalid", level="warning")
            return {"status": "ok"}

        await _process_webhook_payload(payload)

        return {"status": "ok"}

    except Exception as e:
        log_exception("webhook_unhandled_error", e, endpoint="POST /webhook")
        return {"status": "ok"}


def _verify_signature(body: bytes, signature: Optional[str]) -> bool:
    """
    Verify webhook authenticity using HMAC-SHA256.
    """
    if settings.ENV == "development" and not settings.META_APP_SECRET:
        return True

    if not signature or not signature.startswith("sha256="):
        return False

    expected_signature = signature[7:]
    app_secret = settings.META_APP_SECRET
    if not app_secret:
        log_event("webhook_secret_missing", level="error")
        return False

    computed = hmac.new(
        key=app_secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(computed, expected_signature)


def _is_valid_payload(payload: dict) -> bool:
    """
    Validate minimum WhatsApp webhook structure.
    """
    try:
        if payload.get("object") != "whatsapp_business_account":
            return False

        entries = payload.get("entry")
        if not isinstance(entries, list) or len(entries) == 0:
            return False

        for entry in entries:
            changes = entry.get("changes")
            if not isinstance(changes, list) or len(changes) == 0:
                return False

            for change in changes:
                if "value" not in change:
                    return False

        return True
    except Exception:
        return False


async def _process_webhook_payload(payload: dict) -> None:
    """
    Process webhook payload and route events to appropriate queues.
    """
    for entry in payload.get("entry", []):
        waba_id = entry.get("id")

        for change in entry.get("changes", []):
            field = change.get("field", "messages")
            value = change.get("value", {})
            metadata = value.get("metadata", {})
            phone_number_id = metadata.get("phone_number_id")

            await _route_change_to_queue(
                waba_id=waba_id,
                phone_number_id=phone_number_id,
                field=field,
                value=value,
                full_payload=payload,
            )


async def _route_change_to_queue(
    waba_id: str,
    phone_number_id: Optional[str],
    field: str,
    value: dict,
    full_payload: dict,
) -> None:
    """
    Route a single change to the appropriate Redis queue.
    """
    if "messages" in value:
        for message in value["messages"]:
            await _queue_message_event(
                waba_id=waba_id,
                phone_number_id=phone_number_id,
                message=message,
                contacts=value.get("contacts", []),
                metadata=value.get("metadata", {}),
            )

    if "statuses" in value:
        for status in value["statuses"]:
            await _queue_status_event(
                waba_id=waba_id,
                phone_number_id=phone_number_id,
                status=status,
                metadata=value.get("metadata", {}),
            )

    if "errors" in value:
        for error in value["errors"]:
            await _queue_error_event(
                waba_id=waba_id, phone_number_id=phone_number_id, error=error
            )

    if field in ("template_category_update", "message_template_status_update"):
        await _queue_template_event(waba_id=waba_id, field=field, value=value)

    if "history" in value:
        log_event(
            "webhook_history_received", waba_id=waba_id, phone_number_id=phone_number_id
        )

    if "events" in value:
        log_event(
            "webhook_tracking_received",
            waba_id=waba_id,
            phone_number_id=phone_number_id,
            events_count=len(value["events"]),
        )


async def _queue_message_event(
    waba_id: str,
    phone_number_id: Optional[str],
    message: dict,
    contacts: list,
    metadata: dict,
) -> None:
    """Queue incoming message."""
    wa_message_id = message.get("id")
    if not wa_message_id:
        return

    idempotency_key = key_idempotency(waba_id, wa_message_id)
    if await is_duplicate(idempotency_key):
        log_event("webhook_duplicate_message", wa_message_id=wa_message_id)
        return

    contact_info = contacts[0] if contacts else {}

    event = {
        "type": WebhookEventType.MESSAGE.value,
        "waba_id": waba_id,
        "phone_number_id": phone_number_id,
        "wa_message_id": wa_message_id,
        "from": message.get("from"),
        "timestamp": message.get("timestamp"),
        "message_type": message.get("type"),
        "message": message,
        "contact": {
            "wa_id": contact_info.get("wa_id"),
            "name": contact_info.get("profile", {}).get("name"),
        },
        "metadata": metadata,
    }

    is_interactive = message.get("type") in ("interactive", "button")
    queue = Queue.HIGH_PRIORITY if is_interactive else Queue.INBOUND_WEBHOOKS

    if await enqueue(queue, event):
        log_event(
            "webhook_message_queued",
            wa_message_id=wa_message_id,
            message_type=message.get("type"),
            queue=queue.value,
        )
    else:
        log_event(
            "webhook_message_queue_failed", level="error", wa_message_id=wa_message_id
        )


async def _queue_status_event(
    waba_id: str, phone_number_id: Optional[str], status: dict, metadata: dict
) -> None:
    """Queue message status update."""
    wa_message_id = status.get("id")
    status_value = status.get("status")

    if not wa_message_id or not status_value:
        return

    idempotency_key = key_idempotency(waba_id, f"{wa_message_id}:{status_value}")
    if await is_duplicate(idempotency_key):
        log_event(
            "webhook_duplicate_status", wa_message_id=wa_message_id, status=status_value
        )
        return

    event = {
        "type": WebhookEventType.STATUS.value,
        "waba_id": waba_id,
        "phone_number_id": phone_number_id,
        "wa_message_id": wa_message_id,
        "status": status_value,
        "timestamp": status.get("timestamp"),
        "recipient_id": status.get("recipient_id"),
        "pricing": status.get("pricing"),
        "conversation": status.get("conversation"),
        "errors": status.get("errors"),
        "metadata": metadata,
    }

    if await enqueue(Queue.MESSAGE_STATUS, event):
        log_event(
            "webhook_status_queued", wa_message_id=wa_message_id, status=status_value
        )


async def _queue_error_event(
    waba_id: str, phone_number_id: Optional[str], error: dict
) -> None:
    """Queue error event."""
    event = {
        "type": WebhookEventType.ERROR.value,
        "waba_id": waba_id,
        "phone_number_id": phone_number_id,
        "code": error.get("code"),
        "title": error.get("title"),
        "message": error.get("message"),
        "error_data": error.get("error_data"),
    }

    await enqueue(Queue.HIGH_PRIORITY, event)

    log_event(
        "webhook_error_queued",
        level="warning",
        error_code=error.get("code"),
        error_title=error.get("title"),
    )


async def _queue_template_event(waba_id: str, field: str, value: dict) -> None:
    """Queue template status change."""
    event = {
        "type": WebhookEventType.TEMPLATE_STATUS.value,
        "waba_id": waba_id,
        "field": field,
        "event": value.get("event"),
        "message_template_id": value.get("message_template_id"),
        "message_template_name": value.get("message_template_name"),
        "message_template_language": value.get("message_template_language"),
        "reason": value.get("reason"),
    }

    await enqueue(Queue.TEMPLATE_SYNC, event)

    log_event(
        "webhook_template_queued",
        template_name=value.get("message_template_name"),
        event=value.get("event"),
    )
