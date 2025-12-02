"""
Webhook Endpoint - app/api/webhooks.py

Single entry point for all Meta WhatsApp events (Messages, Statuses, Template changes).

ARCHITECTURE:
    - Decoupled: Webhook acts as an ingestion layer only.
    - Synchronous: Validates signature, checks idempotency, pushes to Redis (< 500ms).
    - Asynchronous: Workers process the logic (DB writes, logic) to prevent timeouts.

CRITICAL CONSTRAINTS:
    - Must respond with 200 OK within 3 seconds to prevent Meta retries.
    - Must return 200 OK even on processing errors (log & continue).
    - Must handle duplicate events via Event ID (Idempotency).
    - Must verify X-Hub-Signature-256 (Security).

ENDPOINTS:
    - GET /webhook: Meta verification challenge (Setup only).
    - POST /webhook: Event ingestion.
"""

from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
import json
import hmac
import hashlib
from server.core.config import settings
# from server.core.redis import get_redis, QueueNames
# from server.whatsapp.parser import webhook_parser
# from app.utils.idempotency import is_duplicate
# from app.core.monitoring import log_event, log_exception

router = APIRouter(tags=["Webhooks"])


@router.get("/webhook")
async def verify_webhook(
    request: Request
):
    """
    Webhook Verification (Setup Only)
    
    Meta calls this ONCE when you first configure the webhook.
    Must return the challenge value to verify ownership.
    
    Query Parameters (from Meta):
        hub.mode: "subscribe"
        hub.verify_token: Your secret token
        hub.challenge: Random string to echo back
    """
    # Get query parameters
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    # Verify parameters
    if mode == "subscribe" and token == settings.META_WEBHOOK_VERIFY_TOKEN:
        # Token matches - return challenge to verify
        # log_event("webhook_verified", {"mode": mode})
        print("webhook_verified", {"mode": mode})
        return int(challenge)  # Must return as integer
    else:
        # Token doesn't match - reject
        log_event("webhook_verification_failed", {
            "mode": mode,
            "token_provided": bool(token)
        })
        raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None)
):
    """
    Main Webhook Endpoint - Receives ALL events from Meta
    
    Flow: Validate -> Check Idempotency -> Queue to Redis -> Return 200
    """
    
    try:
        # Step 1: Read raw body (needed for signature verification)
        body = await request.body()
        
        # Step 2: Verify signature (security check)
        # TODO: Uncomment in production!
        # if not verify_signature(body, x_hub_signature_256):
        #     log_event("webhook_invalid_signature")
        #     raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Step 3: Parse JSON payload
        payload = json.loads(body)
        
        # Step 4: Validate payload structure
        if not webhook_parser.is_valid_webhook(payload):
            print("webhook_invalid_payload", {"payload": payload})
            return {"status": "ok"}  # Still return 200 to Meta
        
        # Step 5: Get event ID for idempotency
        event_id = webhook_parser.get_event_id(payload)
        
        # Step 6: Check if we've already processed this
        if event_id and await is_duplicate(event_id):
            print("webhook_duplicate", {"event_id": event_id})
            return {"status": "ok"}  # Already processed, skip
        
        # Step 7: Determine event type and route to appropriate queue
        # await route_webhook_to_queue(payload)
        
        # Step 8: Log success
        print("webhook_received", {
            "event_id": event_id,
            "object": payload.get("object")
        })
        
        # Step 9: Return success to Meta (FAST!)
        return {"status": "ok"}
        
    except json.JSONDecodeError:
        print(Exception("Invalid JSON in webhook"))
        return {"status": "ok"}  # Still return 200 to Meta
        
    except Exception as e:
        # Log error but still return 200 to Meta
        # Don't want Meta to keep retrying due to our errors
        print(e, {"endpoint": "webhook"})
        return {"status": "ok"}


async def route_webhook_to_queue(payload: dict):
    """
    Route webhook to appropriate Redis queue based on event type.
    """
    redis = await get_redis()
    
    # Extract all messages
    messages = webhook_parser.extract_messages(payload)
    if messages:
        for message in messages:
            # Queue each message for processing
            await redis.lpush(
                QueueNames.WEBHOOK_PROCESSING,
                json.dumps({
                    "type": "message",
                    "data": message,
                    "payload": payload  # Full payload for context
                })
            )
    
    # Extract all status updates
    statuses = webhook_parser.extract_statuses(payload)
    if statuses:
        for status in statuses:
            # Queue each status update
            await redis.lpush(
                QueueNames.WEBHOOK_PROCESSING,
                json.dumps({
                    "type": "status",
                    "data": status,
                    "payload": payload
                })
            )
    
    # Check for template status updates
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            
            # Template status update
            if "message_template_status_update" in value:
                await redis.lpush(
                    QueueNames.WEBHOOK_PROCESSING,
                    json.dumps({
                        "type": "template_status",
                        "data": value["message_template_status_update"],
                        "payload": payload
                    })
                )
            
            # Phone number quality update
            if "phone_number_quality_update" in value:
                await redis.lpush(
                    QueueNames.WEBHOOK_PROCESSING,
                    json.dumps({
                        "type": "quality_update",
                        "data": value["phone_number_quality_update"],
                        "payload": payload
                    })
                )


def verify_signature(body: bytes, signature: Optional[str]) -> bool:
    """
    Verify webhook came from Meta using HMAC signature.
    """
    if not signature:
        return False
    
    # Extract signature from header (format: "sha256=xxxxx")
    try:
        method, signature_hash = signature.split("=")
        if method != "sha256":
            return False
    except ValueError:
        return False
    
    # Calculate expected signature
    # TODO: Add APP_SECRET to settings
    app_secret = settings.META_WEBHOOK_VERIFY_TOKEN  # Use app secret instead
    # expected_signature = hmac.new(
    #     app_secret.encode(),
    #     body,
    #     hashlib.sha256
    # ).hexdigest()
    
    # Compare signatures (timing-safe comparison)
    # return hmac.compare_digest(signature_hash, expected_signature)
    return app_secret == signature_hash