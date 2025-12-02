import os
import json
from datetime import datetime
from server.core.config import settings

from fastapi import APIRouter, FastAPI, Request, Response, HTTPException

router = APIRouter()

# 1. Configuration
VERIFY_TOKEN = settings.META_WEBHOOK_VERIFY_TOKEN
print(VERIFY_TOKEN)
PORT = settings.PORT
LOG_FILE = "whatsapp_webhook_log.txt"

def append_log(payload: dict):
    """
    Appends the webhook payload to a text file in a neat format.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Try to identify the event type for the header
    event_type = "Unknown Event"
    try:
        changes = payload.get("entry", [])[0].get("changes", [])[0].get("value", {})
        if "messages" in changes:
            event_type = "📨 INCOMING MESSAGE"
        elif "statuses" in changes:
            event_type = "✅ MESSAGE STATUS UPDATE"
        elif "message_template_status_update" in changes:
            event_type = "📝 TEMPLATE UPDATE"
    except:
        pass

    # Create a neat divider
    log_entry = (
        f"\n"
        f"==================================================\n"
        f"📅 TIME: {timestamp} | TYPE: {event_type}\n"
        f"==================================================\n"
        f"{json.dumps(payload, indent=4)}\n"
    )

    # Append to file (mode='a')
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

@router.get("/")
async def verify_webhook(request: Request):
    """
    Handle the Webhook Verification (GET)
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ WEBHOOK VERIFIED")
        return Response(content=challenge, media_type="text/plain")
    
    print("❌ VERIFICATION FAILED")
    raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/")
async def receive_webhook(request: Request):
    """
    Handle Incoming Events (POST)
    Logs to file and returns 200 OK.
    """
    try:
        payload = await request.json()
        
        # 1. Write to file
        append_log(payload)
        
        # 2. Print to console (so you see it happening live)
        print(f"✅ Event logged to {LOG_FILE}")
        
        return {"status": "received"}
        
    except Exception as e:
        print(f"⚠️ Error processing webhook: {e}")
        return {"status": "error"} # Still return 200 equivalent