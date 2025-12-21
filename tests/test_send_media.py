"""
WhatsApp Media Message Test & Debugger
Test script for sending media messages (image, video, audio, document, sticker)
"""

import asyncio

# Suppress SQLAlchemy logging
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
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


async def test_send_media():
    """Test media message sending with debugging."""
    await redis_startup()

    try:
        # =====================================================================
        # INPUT
        # =====================================================================
        print("\n📝 Enter Details:")
        workspace_id = input("   Workspace ID (UUID): ").strip()
        phone_number_id = input("   Phone Number ID (UUID from DB): ").strip()
        to_number = input("   Recipient Number (+country...): ").strip()

        print("\n📎 Media Type Options:")
        print("   1. image")
        print("   2. video")
        print("   3. audio")
        print("   4. document")
        print("   5. sticker")
        media_type = input("   Enter media type (or number 1-5): ").strip().lower()

        # Map number to type
        type_map = {
            "1": "image",
            "2": "video",
            "3": "audio",
            "4": "document",
            "5": "sticker",
        }
        media_type = type_map.get(media_type, media_type)

        if media_type not in ["image", "video", "audio", "document", "sticker"]:
            print(f"❌ Invalid media type: {media_type}")
            return

        print(f"\n🔗 Media Source (provide ONE):")
        media_url = input("   Media URL (public HTTPS link): ").strip() or None
        media_id = (
            input("   OR Internal Media UUID (from media_files table): ").strip()
            or None
        )

        if not media_url and not media_id:
            print("❌ Must provide either media_url or media_id")
            return

        caption = None
        filename = None
        if media_type in ["image", "video", "document"]:
            caption = (
                input("   Caption (optional, press Enter to skip): ").strip() or None
            )
        if media_type == "document":
            filename = (
                input("   Filename (optional, e.g., 'report.pdf'): ").strip() or None
            )

        # =====================================================================
        # PHONE VERIFICATION
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
                print("❌ Phone number not found!")
                print(f"   • Phone ID: {phone_number_id}")
                print(f"   • Workspace: {workspace_id}")
                return

            print(f"✅ {phone.display_name} ({phone.phone_number})")
            print(f"   • Meta Phone ID: {phone.phone_number_id}")
            print(
                f"   • Access Token: {'✓ Present' if phone.access_token else '✗ MISSING'}"
            )

            if not phone.access_token:
                print("\n⚠️  No access token!")
                return

        # =====================================================================
        # ENQUEUE MEDIA MESSAGE
        # =====================================================================
        print_section("Step 2: Enqueueing Media Message")

        message_id = str(uuid.uuid4())
        print(f"   Message ID: {message_id}")
        print(f"   Media Type: {media_type}")
        print(f"   Source: {'URL' if media_url else 'Media ID'}")

        payload = {
            "type": "media_message",
            "message_id": message_id,
            "workspace_id": workspace_id,
            "phone_number_id": phone.phone_number_id,
            "to_number": to_number,
            "media_type": media_type,
        }

        if media_url:
            payload["media_url"] = media_url
        if media_id:
            payload["media_id"] = media_id
        if caption:
            payload["caption"] = caption
        if filename:
            payload["filename"] = filename

        success = await enqueue(Queue.OUTBOUND_MESSAGES, payload)

        if not success:
            print("❌ Failed to enqueue!")
            return

        print("✅ Enqueued successfully")
        print(f"   Queued at: {datetime.now().strftime('%H:%M:%S')}")

        # =====================================================================
        # WAIT
        # =====================================================================
        print_section("Step 3: Waiting for Worker")
        print("⏳ Waiting 10 seconds...")

        for i in range(10, 0, -1):
            print(f"   {i}...", end="\r")
            await asyncio.sleep(1)
        print("   Done!   ")

        # =====================================================================
        # RESULT
        # =====================================================================
        print_section("Step 4: Verifying Result")

        async with async_session_maker() as session:
            message = await session.scalar(
                select(Message).where(Message.id == uuid.UUID(message_id))
            )

            if not message:
                print("❌ NOT IN DATABASE")
                print("   → Worker not running or crashed")
                print("   → Check worker terminal for errors")

            elif message.status == "sent":
                print("✅ MEDIA SENT SUCCESSFULLY!")
                print(f"\n   📱 WhatsApp Message ID: {message.wa_message_id}")
                print(f"   📎 Media Type: {media_type}")
                print(f"   📤 To: {message.to_number}")
                print(
                    f"   🕐 Sent at: {message.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
                )

            elif message.status == "failed":
                print("❌ MEDIA SEND FAILED")
                print(f"\n   Error Code: {message.error_code}")
                print(f"   Error: {message.error_message}")

                # Common media errors
                if "131053" in str(message.error_code):
                    print("\n💡 FIX: Media URL not accessible")
                    print("   → Ensure URL is publicly accessible (HTTPS)")
                    print("   → Check URL is not expired")
                elif "131052" in str(message.error_code):
                    print("\n💡 FIX: Media type not supported")
                    print("   → Check file format is supported by WhatsApp")
                elif "131045" in str(message.error_code):
                    print("\n💡 FIX: Media file too large")
                    print(
                        "   → Image: max 5MB | Video: max 16MB | Audio: max 16MB | Document: max 100MB"
                    )
                elif "190" in str(message.error_code):
                    print("\n💡 FIX: Access token expired")
                    print("   → Regenerate token in Meta Business Manager")

            else:
                print(f"⏳ Status: {message.status}")

        # =====================================================================
        # QUEUE STATS
        # =====================================================================
        print_section("Queue Statistics")

        from server.core.redis import get_redis

        redis = await get_redis()
        outbound = await redis.llen(Queue.OUTBOUND_MESSAGES.value)
        dlq = await redis.llen(Queue.DEAD_LETTER.value)

        print(f"   Outbound: {outbound} pending")
        print(f"   Dead Letter: {dlq} failed")

        if dlq > 0:
            print(f"\n   ⚠️  {dlq} messages in DLQ")

        print()

    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled")
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await redis_shutdown()


if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")

    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 14 + "WhatsApp Media Message Tester" + " " * 15 + "║")
    print("╚" + "═" * 58 + "╝")

    print("\n✓ Supported Media Types:")
    print("  • image  - JPEG, PNG (max 5MB)")
    print("  • video  - MP4, 3GPP (max 16MB)")
    print("  • audio  - AAC, MP3, OGG, AMR (max 16MB)")
    print("  • document - PDF, DOC, XLS, etc (max 100MB)")
    print("  • sticker - WebP, animated WebP (max 500KB)")

    print("\n✓ Prerequisites:")
    print("  • Worker running: python -m server.workers.outbound")
    print("  • Valid access token in database")
    print("  • Public HTTPS URL for media OR Meta media_id")

    asyncio.run(test_send_media())
