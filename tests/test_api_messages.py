"""
API Message Sending Test Script
Tests the actual API endpoints for sending messages.
"""

import asyncio
import os

import httpx

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api")


async def test_send_text():
    """Test sending a text message via API."""
    print("\n" + "=" * 60)
    print("WhatsApp Text Message API Test")
    print("=" * 60)

    # Get auth token (you need to login first)
    print("\n📝 Enter Details:")
    auth_token = input("   Auth Token (JWT): ").strip()
    workspace_id = input("   Workspace ID (UUID): ").strip()
    phone_number_id = input("   Phone Number ID (DB UUID): ").strip()
    to_number = input("   Recipient Number (+country...): ").strip()
    text = input("   Message Text: ").strip()

    if not all([auth_token, workspace_id, phone_number_id, to_number, text]):
        print("❌ All fields are required")
        return

    # Send request
    print("\n" + "-" * 60)
    print("  Sending to API...")
    print("-" * 60)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/messages/send/text",
            json={
                "workspace_id": workspace_id,
                "phone_number_id": phone_number_id,
                "to": to_number,
                "text": text,
            },
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    print(f"\n   Status: {response.status_code}")

    if response.status_code == 201:
        data = response.json()
        print("✅ Message Queued!")
        print(f"   • Message ID: {data['id']}")
        print(f"   • To: {data['to_number']}")
        print(f"   • Status: {data['status']}")
        print(f"   • Queued: {data['queued']}")
        print("\n💡 Check worker terminal for processing status")
    else:
        print("❌ Failed!")
        try:
            error = response.json()
            print(f"   Error: {error}")
        except:
            print(f"   Response: {response.text}")


async def test_send_media():
    """Test sending a media message via API."""
    print("\n" + "=" * 60)
    print("WhatsApp Media Message API Test")
    print("=" * 60)

    print("\n📝 Enter Details:")
    auth_token = input("   Auth Token (JWT): ").strip()
    workspace_id = input("   Workspace ID (UUID): ").strip()
    phone_number_id = input("   Phone Number ID (DB UUID): ").strip()
    media_id = input("   Media File ID (from media_files table): ").strip()
    to_number = input("   Recipient Number (+country...): ").strip()

    print("\n📎 Media Types: image, video, audio, document")
    media_type = input("   Media Type: ").strip().lower()
    caption = input("   Caption (optional): ").strip() or None

    if not all(
        [auth_token, workspace_id, phone_number_id, media_id, to_number, media_type]
    ):
        print("❌ Required fields missing")
        return

    print("\n" + "-" * 60)
    print("  Sending to API...")
    print("-" * 60)

    payload = {
        "workspace_id": workspace_id,
        "phone_number_id": phone_number_id,
        "to": to_number,
        "media_type": media_type,
        "media_id": media_id,
    }
    if caption:
        payload["caption"] = caption

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/messages/send/media",
            json=payload,
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    print(f"\n   Status: {response.status_code}")

    if response.status_code == 201:
        data = response.json()
        print("✅ Media Message Queued!")
        print(f"   • Message ID: {data['id']}")
        print(f"   • To: {data['to_number']}")
        print(f"   • Type: {data['type']}")
        print(f"   • Status: {data['status']}")
        print("\n💡 Check worker terminal for processing status")
    else:
        print("❌ Failed!")
        try:
            error = response.json()
            print(f"   Error: {error}")
        except:
            print(f"   Response: {response.text}")


def main():
    print("\n╔" + "═" * 56 + "╗")
    print("║" + " " * 14 + "WhatsApp API Message Tester" + " " * 15 + "║")
    print("╚" + "═" * 56 + "╝")

    print("\n✓ Prerequisites:")
    print("  • Server running: python run.py")
    print("  • Worker running: python -m server.workers.outbound")
    print("  • Valid auth token (from /api/auth/login)")

    print("\n📋 Select Test:")
    print("   1. Send Text Message")
    print("   2. Send Media Message")
    print("   3. Exit")

    choice = input("\n   Enter choice (1-3): ").strip()

    if choice == "1":
        asyncio.run(test_send_text())
    elif choice == "2":
        asyncio.run(test_send_media())
    else:
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()
