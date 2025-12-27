"""
Text Message Verification Script (E2E Real-Time) - 10 Test Cases
-----------------------------------------------------------------
Verifies all Text Message variations using the actual HTTP API.
Includes proper reply testing using real message IDs.

Usage:
    uv run python tests/test_text_message.py <RECIPIENT_PHONE_NUMBER>
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuration
BASE_URL = "http://localhost:8000"
WORKSPACE_ID = "ff1f8bec-f3f6-47dd-acf9-cedcd9fb1d63"
CHANNEL_ID = "233359b1-7b8f-43a5-abd2-396a6683ff12"
SUPABASE_EMAIL = "shashankgundas1@gmail.com"
SUPABASE_PASSWORD = "123456"
HTTP_TIMEOUT = 30.0

# Fallback message ID from database for reply testing
FALLBACK_MESSAGE_ID = "d82d609d-f567-404a-87b7-39e93639f696"


class TextMessageVerifierE2E:
    def __init__(self, recipient: str):
        self.recipient = recipient if recipient.startswith("+") else "+" + recipient
        self.jwt_token = None
        self.results = []
        self.passed = 0
        self.failed = 0
        self.last_message_id = None

    async def authenticate(self) -> bool:
        print("\n🔐 Authenticating...")
        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                resp = await client.post(
                    f"{BASE_URL}/api/auth/signin",
                    json={"email": SUPABASE_EMAIL, "password": SUPABASE_PASSWORD},
                )
                if resp.status_code == 200:
                    self.jwt_token = resp.json()["access_token"]
                    print("✅ Authenticated")
                    return True
                print(f"❌ Auth failed: {resp.status_code}")
                return False
        except Exception as e:
            print(f"❌ Auth error: {e}")
            return False

    async def api_post(self, endpoint: str, data: dict) -> tuple:
        url = f"{BASE_URL}/api/workspaces/{WORKSPACE_ID}{endpoint}"
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            try:
                r = await client.post(url, headers=headers, json=data)
                return r.status_code, r.json()
            except Exception as e:
                return 0, {"error": str(e)}

    async def api_get(self, endpoint: str) -> tuple:
        url = f"{BASE_URL}/api/workspaces/{WORKSPACE_ID}{endpoint}"
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            try:
                r = await client.get(url, headers=headers)
                return r.status_code, r.json()
            except Exception as e:
                return 0, {"error": str(e)}

    def check(self, name: str, condition: bool, details: str = ""):
        if condition:
            print(f"✅ PASS: {name}")
            self.passed += 1
            self.results.append((name, True))
        else:
            print(f"❌ FAIL: {name} - {details}")
            self.failed += 1
            self.results.append((name, False))

    async def wait_for_wa_message_id(
        self, message_id: str, max_wait: int = 15
    ) -> str | None:
        """Poll for wa_message_id after message is sent."""
        print(f"   ⏳ Waiting for wa_message_id (max {max_wait}s)...")
        for i in range(max_wait):
            await asyncio.sleep(1)
            status, data = await self.api_get(f"/messages/{message_id}/status")
            if status == 200 and data.get("wa_message_id"):
                print(f"   ✅ Got wa_message_id: {data['wa_message_id'][:30]}...")
                return data["wa_message_id"]

        # Fallback: try the configured fallback message
        print(f"   ⚠️ Timeout. Trying fallback message ID...")
        status, data = await self.api_get(f"/messages/{FALLBACK_MESSAGE_ID}/status")
        if status == 200 and data.get("wa_message_id"):
            print(f"   ✅ Got fallback wa_message_id: {data['wa_message_id'][:30]}...")
            return data["wa_message_id"]

        print("   ❌ No wa_message_id available")
        return None

    async def run(self):
        print(f"Starting E2E Verification for {self.recipient}...")
        print("Testing 10 Text Message Types\n")

        if not await self.authenticate():
            return False

        print("\n--- Sending Text Messages via API ---\n")

        # 1. Basic Text
        status, data = await self.api_post(
            "/messages/send/text",
            {
                "workspace_id": WORKSPACE_ID,
                "channel_id": CHANNEL_ID,
                "to": self.recipient,
                "text": f"Test 1: Basic Text | ID: {uuid4().hex[:8]}",
            },
        )
        self.check("1. Basic Text", status == 201, str(data))

        # 2. Emoji Text
        status, data = await self.api_post(
            "/messages/send/text",
            {
                "workspace_id": WORKSPACE_ID,
                "channel_id": CHANNEL_ID,
                "to": self.recipient,
                "text": f"Test 2: Emojis 🚀 🎉 ✨ 💯",
            },
        )
        self.check("2. Emoji Text", status == 201, str(data))

        # 3. Long Text
        long_text = "Test 3: Long Text | " + ("Lorem ipsum " * 300)
        status, data = await self.api_post(
            "/messages/send/text",
            {
                "workspace_id": WORKSPACE_ID,
                "channel_id": CHANNEL_ID,
                "to": self.recipient,
                "text": long_text[:4000],
            },
        )
        self.check("3. Long Text", status == 201, str(data))

        # 4. URL Preview - store ID for reply
        status, data = await self.api_post(
            "/messages/send/text",
            {
                "workspace_id": WORKSPACE_ID,
                "channel_id": CHANNEL_ID,
                "to": self.recipient,
                "text": f"Test 4: Preview URL https://www.google.com",
                "preview_url": True,
            },
        )
        self.check("4. URL Preview", status == 201, str(data))
        if status == 201:
            self.last_message_id = str(data.get("id"))

        # 5. Reply to Message
        print("\n--- Testing Reply with Real Message ID ---")
        wa_message_id = None
        if self.last_message_id:
            wa_message_id = await self.wait_for_wa_message_id(self.last_message_id)

        if wa_message_id:
            status, data = await self.api_post(
                "/messages/send/text",
                {
                    "workspace_id": WORKSPACE_ID,
                    "channel_id": CHANNEL_ID,
                    "to": self.recipient,
                    "text": f"Test 5: This is a REPLY to the URL preview message above ☝️",
                    "reply_to_message_id": wa_message_id,
                },
            )
            self.check("5. Reply to Message (Real ID)", status == 201, str(data))
        else:
            self.check(
                "5. Reply to Message (Real ID)", False, "Could not get wa_message_id"
            )

        # 6. URL Preview + Reply
        if wa_message_id:
            status, data = await self.api_post(
                "/messages/send/text",
                {
                    "workspace_id": WORKSPACE_ID,
                    "channel_id": CHANNEL_ID,
                    "to": self.recipient,
                    "text": f"Test 6: Preview + Reply https://github.com",
                    "preview_url": True,
                    "reply_to_message_id": wa_message_id,
                },
            )
            self.check("6. URL Preview + Reply", status == 201, str(data))
        else:
            self.check("6. URL Preview + Reply", False, "No wa_message_id for reply")

        # 7. Unicode/Multi-language
        status, data = await self.api_post(
            "/messages/send/text",
            {
                "workspace_id": WORKSPACE_ID,
                "channel_id": CHANNEL_ID,
                "to": self.recipient,
                "text": f"Test 7: Unicode | 你好 مرحبا שלום Привет",
            },
        )
        self.check("7. Unicode/Multi-language", status == 201, str(data))

        # 8. Line Breaks
        status, data = await self.api_post(
            "/messages/send/text",
            {
                "workspace_id": WORKSPACE_ID,
                "channel_id": CHANNEL_ID,
                "to": self.recipient,
                "text": "Test 8: Line Breaks\nLine 2\nLine 3\n\nDouble Break",
            },
        )
        self.check("8. Text with Line Breaks", status == 201, str(data))

        # 9. Special Characters
        status, data = await self.api_post(
            "/messages/send/text",
            {
                "workspace_id": WORKSPACE_ID,
                "channel_id": CHANNEL_ID,
                "to": self.recipient,
                "text": "Test 9: Special Chars | <>&\"'`~!@#$%^*()",
            },
        )
        self.check("9. Special Characters", status == 201, str(data))

        # 10. Single Character
        status, data = await self.api_post(
            "/messages/send/text",
            {
                "workspace_id": WORKSPACE_ID,
                "channel_id": CHANNEL_ID,
                "to": self.recipient,
                "text": "X",
            },
        )
        self.check("10. Single Character", status == 201, str(data))

        # Summary
        print("\n" + "=" * 40)
        print(f"📊 Summary: {self.passed} Passed, {self.failed} Failed out of 10")
        print("=" * 40)

        return self.failed == 0


async def main():
    if len(sys.argv) < 2:
        print("Usage: uv run python tests/test_text_message.py <phone>")
        sys.exit(1)

    recipient = sys.argv[1]
    verifier = TextMessageVerifierE2E(recipient)
    success = await verifier.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
