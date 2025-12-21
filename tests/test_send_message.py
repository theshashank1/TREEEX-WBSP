"""
WhatsApp Outbound Message Test & Debugger
Production-ready test script with comprehensive error diagnostics
"""

import asyncio

# Suppress SQLAlchemy query logging for cleaner output
import logging
import os
import uuid
from datetime import datetime

from sqlalchemy import select

from server.core.db import async_session_maker
from server.core.redis import Queue, enqueue
from server.core.redis import shutdown as redis_shutdown
from server.core.redis import startup as redis_startup
from server.models.contacts import PhoneNumber
from server.models.messaging import Message

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def print_error_solution(error_code: str, error_msg: str):
    """Print targeted solution based on error code."""
    solutions = {
        "190": {
            "issue": "Access Token Expired",
            "steps": [
                "Go to Meta Business Manager (business.facebook.com)",
                "Navigate to: Business Settings → System Users",
                "Select your system user and generate new token",
                "Update DB: UPDATE phone_numbers SET access_token='NEW_TOKEN' WHERE id='...'",
            ],
        },
        "131031": {
            "issue": "Account Restricted/Flagged",
            "steps": [
                "Check Meta Business Suite for account status",
                "Review WhatsApp Business Policy compliance",
                "Contact Meta support if account is blocked",
            ],
        },
        "131005": {
            "issue": "Phone Number Not Registered",
            "steps": [
                "Verify phone number is registered in WhatsApp Business",
                "Check phone_number_id matches Meta's configuration",
                "Ensure WhatsApp Business API is properly set up",
            ],
        },
        "100": {
            "issue": "Invalid Parameter",
            "steps": [
                "Check phone number format (E.164: +country...)",
                "Verify all required fields are present",
                "Review message schema validation",
            ],
        },
    }

    solution = solutions.get(str(error_code))
    if solution:
        print(f"\n💡 SOLUTION: {solution['issue']}")
        for i, step in enumerate(solution["steps"], 1):
            print(f"   {i}. {step}")
    else:
        print(f"\n💡 Error {error_code}: Check Meta API documentation for details")


async def test_send_message():
    """Test outbound message with comprehensive debugging."""
    await redis_startup()

    try:
        # =====================================================================
        # INPUT & VALIDATION
        # =====================================================================
        print("\n📝 Enter Details:")
        workspace_id = input("   Workspace ID (UUID): ").strip()
        phone_number_id = input("   Phone Number ID (UUID from DB): ").strip()
        to_number = input("   Recipient Number (+country...): ").strip()

        # =====================================================================
        # PHONE NUMBER VERIFICATION
        # =====================================================================
        print_section("Step 1: Verifying Phone Number")

        async with async_session_maker() as session:
            phone = await session.scalar(
                select(PhoneNumber).where(
                    PhoneNumber.id == uuid.UUID(phone_number_id),
                    PhoneNumber.workspace_id == uuid.UUID(workspace_id),
                    PhoneNumber.deleted_at.is_(None),
                )
            )

            if not phone:
                print("❌ Phone number not found in database!")
                print(f"\n   Searched for:")
                print(f"   • Phone ID: {phone_number_id}")
                print(f"   • Workspace: {workspace_id}")
                print(f"\n   Troubleshooting:")
                print(f"   1. Verify UUIDs are correct (check phone_numbers table)")
                print(f"   2. Ensure phone_number belongs to workspace")
                print(f"   3. Check deleted_at IS NULL")
                return

            print("✅ Phone number found")
            print(f"   • Display Name: {phone.display_name}")
            print(f"   • Phone: {phone.phone_number}")
            print(f"   • Meta Phone ID: {phone.phone_number_id}")
            print(f"   • Business ID: {phone.business_id or 'Not set'}")
            print(f"   • Status: {phone.status}")
            print(
                f"   • Access Token: {'✓ Present' if phone.access_token else '✗ MISSING'}"
            )

            if not phone.access_token:
                print("\n⚠️  CRITICAL: No access token - message will fail!")
                return

        # =====================================================================
        # MESSAGE ENQUEUE
        # =====================================================================
        print_section("Step 2: Enqueueing Message")

        message_id = str(uuid.uuid4())
        print(f"   Message ID: {message_id}")

        payload = {
            "type": "text_message",
            "message_id": message_id,
            "workspace_id": workspace_id,
            "phone_number_id": phone.phone_number_id,  # Meta's ID, not our UUID
            "to_number": to_number,
            "text": "🧪 Test message from WhatsApp Outbound Worker",
            "preview_url": False,
        }

        success = await enqueue(Queue.OUTBOUND_MESSAGES, payload)

        if not success:
            print("❌ Failed to enqueue to Redis!")
            print("   → Check Redis connection and configuration")
            return

        print("✅ Enqueued successfully")
        print(f"   Queued at: {datetime.now().strftime('%H:%M:%S')}")

        # =====================================================================
        # PROCESSING WAIT
        # =====================================================================
        print_section("Step 3: Waiting for Worker")
        print("⏳ Waiting 10 seconds for worker to process...")

        for i in range(10, 0, -1):
            print(f"   {i}...", end="\r")
            await asyncio.sleep(1)
        print("   Done!   ")

        # =====================================================================
        # RESULT VERIFICATION
        # =====================================================================
        print_section("Step 4: Verifying Result")

        async with async_session_maker() as session:
            message = await session.scalar(
                select(Message).where(Message.id == uuid.UUID(message_id))
            )

            if not message:
                print(f"   WhatsApp Message ID: {message.wa_message_id or 'None'}")
                print(f"   Error Code: {message.error_code or 'None'}")
                print(f"   Error Message: {message.error_message or 'None'}")

                if message.status == "sent":
                    print("\n✅ SUCCESS! Message sent successfully")
                elif message.status == "failed":
                    print(f"\n❌ FAILED: {message.error_message}")
                elif message.status == "pending":
                    print("\n⏳ Still pending - worker might be slow or blocked")

        # Check queue lengths
        print("\n🔍 Checking queue stats...")
        from server.core.redis import get_redis

        redis = await get_redis()
        outbound_len = await redis.llen(Queue.OUTBOUND_MESSAGES.value)
        dlq_len = await redis.llen(Queue.DEAD_LETTER.value)

        print(f"   Outbound queue: {outbound_len} messages")
        print(f"   Dead Letter Queue: {dlq_len} messages")

        if dlq_len > 0:
            print("\n⚠️  Messages in DLQ - check worker logs for errors")

    finally:
        await redis_shutdown()


if __name__ == "__main__":
    print("=" * 60)
    print("WhatsApp Outbound Message Test")
    print("=" * 60)
    print("\nMake sure:")
    print("1. Outbound worker is running: python -m server.workers.outbound")
    print("2. You have a phone number configured in your workspace")
    print("3. The phone number has a valid access_token")
    print("=" * 60)
    print()

    asyncio.run(test_send_message())
