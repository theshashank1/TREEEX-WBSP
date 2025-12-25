# WhatsApp Outbound Messaging Worker

Production-ready outbound messaging system for WhatsApp Cloud API.

## Quick Start

### Start the Outbound Worker

```bash
# Single worker
python -m server.workers.outbound

# Multiple workers (recommended for production)
python -m server.workers.outbound --workers 4
```

### Enqueue Messages

Use Pydantic commands for type-safe message creation:

```python
from server.core.redis import Queue, enqueue
from server.schemas.outbound import TextMessage, TemplateMessage, MediaMessage
import uuid

# Text message (with Pydantic validation)
cmd = TextMessage(
    message_id=str(uuid.uuid4()),
    workspace_id=str(workspace_id),
    phone_number_id=str(phone_number_id),
    to_number="+15551234567",
    text="Hello from WhatsApp!",
    preview_url=True,
)
await enqueue(Queue.OUTBOUND_MESSAGES, cmd.model_dump())

# Template message
cmd = TemplateMessage(
    message_id=str(uuid.uuid4()),
    workspace_id=str(workspace_id),
    phone_number_id=str(phone_number_id),
    to_number="+15551234567",
    template_name="hello_world",
    language_code="en",
)
await enqueue(Queue.OUTBOUND_MESSAGES, cmd.model_dump())

# Media message
cmd = MediaMessage(
    message_id=str(uuid.uuid4()),
    workspace_id=str(workspace_id),
    phone_number_id=str(phone_number_id),
    to_number="+15551234567",
    media_type="image",
    media_url="https://example.com/image.jpg",
    caption="Check this out!",
)
await enqueue(Queue.OUTBOUND_MESSAGES, cmd.model_dump())
```

## Message Types

| Type | Description |
|------|-------------|
| `text_message` | Plain text with optional URL preview |
| `template_message` | Pre-approved template (required for business-initiated) |
| `media_message` | Image, video, audio, document, or sticker |
| `interactive_buttons` | Up to 3 quick reply buttons |
| `interactive_list` | List picker with sections |
| `location_message` | Location pin |
| `reaction_message` | Emoji reaction to existing message |
| `mark_as_read` | Mark incoming message as read (blue checkmarks) |

## Admin Endpoints

```
GET  /api/admin/health              # System health check
GET  /api/admin/queues/stats        # Queue statistics
GET  /api/admin/messages/{id}       # Inspect message state
GET  /api/admin/messages/stats      # Message statistics by status
POST /api/admin/messages/requeue    # Requeue failed messages
```

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  API / Service  │────▶│    Redis Queue   │────▶│ Outbound Worker │
│                 │     │ OUTBOUND_MESSAGES│     │                 │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                              ┌────────────────────────────┼───────────┐
                              ▼                            ▼           ▼
                        ┌──────────┐              ┌──────────┐  ┌──────────┐
                        │ Rate     │              │ WhatsApp │  │ Postgres │
                        │ Limiter  │              │ Cloud API│  │    DB    │
                        └──────────┘              └──────────┘  └──────────┘
```

## Features

- **Idempotency**: Messages with the same `message_id` are only sent once
- **Rate Limiting**: Token bucket limiter per phone number + global limit
- **Retry Logic**: Exponential backoff with jitter for transient errors
- **DB Transactions**: Atomic status updates (pending → sent/failed)
- **Graceful Shutdown**: Completes in-flight messages on SIGTERM
- **Metrics**: Tracks `messages_sent`, `messages_failed`, `avg_latency`

## Files

| File | Purpose |
|------|---------|
| `server/schemas/outbound.py` | Pydantic commands - validation layer |
| `server/whatsapp/renderer.py` | **NEW** - Converts commands to WhatsApp dicts |
| `server/whatsapp/outbound.py` | OutboundClient - HTTP transport |
| `server/workers/outbound.py` | Queue worker with retry logic |
| `server/core/rate_limiter.py` | Token bucket rate limiter |
| `server/api/admin.py` | Admin endpoints |
| `tests/test_renderer.py` | Renderer unit tests |
| `tests/test_outbound.py` | Integration tests |

## Running Tests

```bash
# Renderer tests (unit)
uv run python -m pytest tests/test_renderer.py -v

# Full test suite
uv run python -m pytest tests/ -v
```
