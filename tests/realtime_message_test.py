"""
WhatsApp API Real-Time Test Suite

Tests ALL message types:
- Text messages (basic, emoji, long)
- Template messages (hello_world)
- Location messages
- Interactive buttons
- Interactive lists

Run: uv run python tests/realtime_message_test.py +919492834190
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx

from server.core.redis import Queue, enqueue
from server.schemas.outbound import (
    Button,
    InteractiveButtonsMessage,
    InteractiveListMessage,
    ListRow,
    ListSection,
    LocationMessage,
    TemplateMessage,
    TextMessage,
)

# =============================================================================
# CONFIGURATION
# =============================================================================

WORKSPACE_ID = "ff1f8bec-f3f6-47dd-acf9-cedcd9fb1d63"
CHANNEL_ID = "233359b1-7b8f-43a5-abd2-396a6683ff12"
META_PHONE_NUMBER_ID = "881598551708915"

SUPABASE_EMAIL = "shashankgundas1@gmail.com"
SUPABASE_PASSWORD = "123456"
BASE_URL = "http://localhost:8000"

HTTP_TIMEOUT = 30.0


# =============================================================================
# TEST CLIENT
# =============================================================================


class WhatsAppTestClient:
    """Complete WhatsApp message testing client."""

    def __init__(self, recipient: str):
        self.recipient = recipient
        self.jwt_token = None
        self.results = []
        self.passed = 0
        self.failed = 0

    async def authenticate(self) -> bool:
        """Login and get JWT token."""
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

    async def api(self, method: str, endpoint: str, data: dict = None) -> tuple:
        """Make API call."""
        url = f"{BASE_URL}/api/workspaces/{WORKSPACE_ID}{endpoint}"
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            if method == "POST":
                r = await client.post(url, headers=headers, json=data)
            else:
                r = await client.get(url, headers=headers)
            return r.status_code, r.json() if r.text else {}

    def log_result(self, name: str, success: bool, msg_id: str = None):
        """Log test result."""
        if success:
            print(f"   ✅ Queued: {msg_id}")
            self.results.append((name, "queued"))
            self.passed += 1
        else:
            print(f"   ❌ Failed")
            self.results.append((name, "failed"))
            self.failed += 1

    # =========================================================================
    # API-BASED TESTS
    # =========================================================================

    async def test_text_basic(self):
        """Test: Text message via API."""
        print(f"\n{'='*55}\n📝 Text Message (Basic)\n{'='*55}")
        status, data = await self.api(
            "POST",
            "/messages/send/text",
            {
                "workspace_id": WORKSPACE_ID,
                "channel_id": CHANNEL_ID,
                "to": self.recipient,
                "text": f"🧪 Test: Basic text\nID: {uuid4().hex[:8]}",
            },
        )
        self.log_result("Text (Basic)", status == 201, data.get("id"))

    async def test_text_emoji(self):
        """Test: Text with emojis."""
        print(f"\n{'='*55}\n😀 Text Message (Emoji)\n{'='*55}")
        status, data = await self.api(
            "POST",
            "/messages/send/text",
            {
                "workspace_id": WORKSPACE_ID,
                "channel_id": CHANNEL_ID,
                "to": self.recipient,
                "text": "🎉 Emojis: 🚀💯⚡✨\nUnicode: 你好 مرحبا",
            },
        )
        self.log_result("Text (Emoji)", status == 201, data.get("id"))

    async def test_template(self):
        """Test: Template message (hello_world)."""
        print(f"\n{'='*55}\n📋 Template Message (hello_world)\n{'='*55}")
        status, data = await self.api(
            "POST",
            "/messages/send/template",
            {
                "workspace_id": WORKSPACE_ID,
                "channel_id": CHANNEL_ID,
                "to": self.recipient,
                "template_name": "hello_world",
                "template_language": "en",
            },
        )
        self.log_result("Template (hello_world)", status == 201, data.get("id"))

    # =========================================================================
    # QUEUE-BASED TESTS (for message types without API endpoints)
    # =========================================================================

    async def test_location(self):
        """Test: Location message via queue."""
        print(f"\n{'='*55}\n📍 Location Message\n{'='*55}")
        msg_id = str(uuid4())
        cmd = LocationMessage(
            message_id=msg_id,
            workspace_id=WORKSPACE_ID,
            phone_number_id=META_PHONE_NUMBER_ID,
            to_number=self.recipient,
            latitude=17.3850,
            longitude=78.4867,
            name="Hyderabad",
            address="Telangana, India",
        )
        success = await enqueue(Queue.OUTBOUND_MESSAGES, cmd.model_dump())
        self.log_result("Location", success, msg_id)

    async def test_interactive_buttons(self):
        """Test: Interactive buttons via queue."""
        print(f"\n{'='*55}\n🔘 Interactive Buttons\n{'='*55}")
        msg_id = str(uuid4())
        cmd = InteractiveButtonsMessage(
            message_id=msg_id,
            workspace_id=WORKSPACE_ID,
            phone_number_id=META_PHONE_NUMBER_ID,
            to_number=self.recipient,
            body_text="Choose an option:",
            buttons=[
                Button(id="btn1", title="Option 1"),
                Button(id="btn2", title="Option 2"),
                Button(id="btn3", title="Option 3"),
            ],
            header_text="Quick Poll",
            footer_text="Tap a button",
        )
        success = await enqueue(Queue.OUTBOUND_MESSAGES, cmd.model_dump())
        self.log_result("Interactive Buttons", success, msg_id)

    async def test_interactive_list(self):
        """Test: Interactive list via queue."""
        print(f"\n{'='*55}\n📋 Interactive List\n{'='*55}")
        msg_id = str(uuid4())
        cmd = InteractiveListMessage(
            message_id=msg_id,
            workspace_id=WORKSPACE_ID,
            phone_number_id=META_PHONE_NUMBER_ID,
            to_number=self.recipient,
            body_text="Select from the menu:",
            button_text="View Menu",
            sections=[
                ListSection(
                    title="Category A",
                    rows=[
                        ListRow(id="a1", title="Item A1", description="Description A1"),
                        ListRow(id="a2", title="Item A2", description="Description A2"),
                    ],
                ),
                ListSection(
                    title="Category B",
                    rows=[
                        ListRow(id="b1", title="Item B1", description="Description B1"),
                    ],
                ),
            ],
            header_text="Menu",
            footer_text="Choose wisely",
        )
        success = await enqueue(Queue.OUTBOUND_MESSAGES, cmd.model_dump())
        self.log_result("Interactive List", success, msg_id)

    # =========================================================================
    # RUN ALL TESTS
    # =========================================================================

    async def run_all(self):
        """Run complete test suite."""
        print("\n" + "=" * 60)
        print("🧪 WHATSAPP COMPLETE MESSAGE TEST SUITE")
        print(f"📱 Recipient: {self.recipient}")
        print("=" * 60)

        if not await self.authenticate():
            return False

        # API-based tests
        await self.test_text_basic()
        await self.test_text_emoji()
        await self.test_template()

        # Queue-based tests
        await self.test_location()
        await self.test_interactive_buttons()
        await self.test_interactive_list()

        # Summary
        print("\n" + "=" * 60)
        print("📊 RESULTS")
        print("=" * 60)
        for name, status in self.results:
            icon = "✅" if status == "queued" else "❌"
            print(f"   {icon} {name}: {status}")

        print(f"\n   ✅ Passed: {self.passed}/{len(self.results)}")
        print(f"   ❌ Failed: {self.failed}")
        print("=" * 60)

        if self.failed == 0:
            print("🎉 ALL TESTS PASSED!")
        else:
            print(f"⚠️ {self.failed} test(s) failed")

        return self.failed == 0


# =============================================================================
# MAIN
# =============================================================================


async def main():
    if len(sys.argv) < 2:
        print("Usage: uv run python tests/realtime_message_test.py <phone>")
        sys.exit(1)

    recipient = sys.argv[1]
    if not recipient.startswith("+"):
        recipient = "+" + recipient

    print(f"\n⚠️ Sending 6 test messages to {recipient}")
    if input("Continue? (yes/no): ").lower() != "yes":
        sys.exit(0)

    # Initialize Redis for queue-based tests
    from server.core.redis import close_redis, get_redis

    get_redis()  # Initialize connection

    try:
        client = WhatsAppTestClient(recipient)
        success = await client.run_all()
    finally:
        await close_redis()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Interrupted")
