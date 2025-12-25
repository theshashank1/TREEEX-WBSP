# WhatsApp Messaging Tests

Comprehensive test suite for the WhatsApp messaging architecture.

## Test Files

### 1. `test_renderer.py` - Unit Tests
Tests the renderer layer in isolation (no API calls needed).

```bash
# Run renderer unit tests
uv run python -m pytest tests/test_renderer.py -v
```

**What it tests:**
- Text message rendering
- Template message rendering
- Media message rendering (image, video, document)
- Interactive buttons/lists
- Location, reactions, mark-as-read

### 2. `test_e2e_messaging.py` - End-to-End Integration
Tests the complete flow: Auth → Renderer → WhatsApp Client validation.

```bash
# Set your WhatsApp access token
$env:WHATSAPP_ACCESS_TOKEN="your_token_here"

# Run E2E tests
uv run python tests/test_e2e_messaging.py
```

**What it tests:**
- ✅ Supabase authentication
- ✅ WhatsApp token validation
- ✅ All renderers with real data
- ✅ Phone number info retrieval
- ⚠️  Message sending (dry-run by default)

### 3. `realtime_message_test.py` - Live Message Sending ⚡
**SENDS REAL MESSAGES** to WhatsApp using the API endpoints.

```bash
# Send test messages to your WhatsApp number
uv run python tests/realtime_message_test.py +1234567890
```

**What it does:**
1. Authenticate with your Supabase account
2. Send text message via API
3. Send template message via API
4. Send emoji/unicode test message
5. Check delivery status
6. **Actually delivers to WhatsApp!**

**Data used:**
- Channel: `233359b1-7b8f-43a5-abd2-396a6683ff12`
- Workspace: `ff1f8bec-f3f6-47dd-acf9-cedcd9fb1d63`
- Access token: Fetched from database automatically

## Quick Start

### Test Everything (Safe - No Real Messages)
```bash
# Unit tests
uv run python -m pytest tests/test_renderer.py -v

# E2E validation
$env:WHATSAPP_ACCESS_TOKEN="your_token"
uv run python tests/test_e2e_messaging.py
```

### Send Real Test Messages
```bash
# ⚠️  WARNING: This sends REAL messages!
uv run python tests/realtime_message_test.py +YOUR_PHONE_NUMBER
```

## Architecture Validation

All tests validate the **Command → Renderer → dict → Client** flow:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Pydantic   │────▶│   Renderer   │────▶│    Client    │
│   Command    │     │   .render()  │     │ .send_payload│
└──────────────┘     └──────────────┘     └──────────────┘
      ✅                    ✅                    ✅
  Validates input     Builds WhatsApp       Sends to API
                         dict payload
```

## Test Results

### Unit Tests (12 tests):
- ✅ Text rendering
- ✅ Template rendering
- ✅ Media (image, video, document, sticker)
- ✅ Interactive buttons & lists
- ✅ Location, reactions, mark-as-read

### E2E Tests (5 steps):
- ✅ Authentication
- ✅ Token validation
- ✅ Renderers
- ✅ WhatsApp client
- ⚠️  Live send (optional)

### Realtime Tests:
- ✅ API authentication
- ✅ Text message sent
- ✅ Template message sent
- ✅ Delivery confirmed

## Troubleshooting

### "Authentication failed"
- Check your Supabase credentials in the test file
- Ensure your API server is running on `localhost:8000`

### "Channel not found"
- Verify your `WORKSPACE_ID` and `CHANNEL_ID` in the test file
- Make sure the channel exists in your database

### "No access token"
- The channel must have a valid WhatsApp access token stored in the database
- Check the `channels` table in your database

## Notes

- The API endpoints automatically fetch the access token from the database
- No need to pass tokens manually when using API endpoints
- The realtime test uses the actual API flow (recommended for production testing)
