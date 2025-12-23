# 📚 API Usage Guide

This guide describes the core workflows for using the TREEEX-WBSP API.

## 🔑 Authentication

Most endpoints require a valid Bearer Token.

```bash
# 1. Sign In to get Access Token
curl -X POST http://localhost:8000/api/auth/signin \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secure_password"}'

# Response:
# { "access_token": "ey...", "token_type": "bearer" }
```

**Header Format:** `Authorization: Bearer <your_access_token>`

---

## 🏢 Workspace Management

Everything happens within a **Workspace**. You must create one first.

### Create a Workspace

```bash
curl -X POST http://localhost:8000/api/workspaces/ \
  -H "Authorization: Bearer <token>" \
  -d '{"name": "My Business", "business_id": "optional_meta_id"}'
```

---

## 📨 Sending Messages

### 1. Send Text Message

The simplest message type.

```bash
curl -X POST http://localhost:8000/api/messages/send/text \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "ws_uuid",
    "phone_number_id": "phone_uuid",
    "to": "1234567890",
    "text": "Hello form TREEEX!"
  }'
```

### 2. Send Template Message (Marketing/Utility)

Templates must be approved by Meta first.

```bash
curl -X POST http://localhost:8000/api/messages/send/template \
  -d '{
    "workspace_id": "ws_uuid",
    "phone_number_id": "phone_uuid",
    "to": "1234567890",
    "template_name": "hello_world",
    "language": "en_US",
    "components": []
  }'
```

### 3. Send Media (Image/Video)

First, upload the media to get a handle, then send the message.

**Step A: Upload Media**
```bash
curl -F "file=@image.jpg" \
     -F "workspace_id=ws_uuid" \
     http://localhost:8000/api/media/upload
```

**Step B: Send Message**
```bash
curl -X POST http://localhost:8000/api/messages/send/media \
  -d '{
    "workspace_id": "ws_uuid",
    "phone_number_id": "phone_uuid",
    "to": "1234567890",
    "type": "image",
    "media_id": "<media_uuid_from_step_A>",
    "caption": "Check this out!"
  }'
```

---

## 📢 Campaigns

Broadcasts allow you to send messages to thousands of contacts efficiently.

### 1. Create Campaign
```bash
curl -X POST http://localhost:8000/api/campaigns/ \
  -H "Authorization: Bearer <token>" \
  -d '{
    "name": "Summer Sale",
    "template_name": "summer_promo",
    "workspace_id": "ws_uuid"
  }'
```

### 2. Add Contacts
Upload a list of contacts to the campaign.
```bash
curl -X POST http://localhost:8000/api/campaigns/{id}/contacts \
  -H "Authorization: Bearer <token>" \
  -d '{
    "contacts": ["+1234567890", "+9876543210"]
  }'
```

### 3. Execute Campaign
Starts the campaign. Status moves from `DRAFT` -> `RUNNING`.
```bash
curl -X POST http://localhost:8000/api/campaigns/{id}/execute \
  -H "Authorization: Bearer <token>"
```

### 4. Pause Campaign
Pause a running campaign (Status -> `SCHEDULED`).
```bash
curl -X POST http://localhost:8000/api/campaigns/{id}/pause \
  -H "Authorization: Bearer <token>"
```

### 5. Cancel Campaign
Permanently cancel a campaign (Status -> `CANCELLED`).
```bash
curl -X POST http://localhost:8000/api/campaigns/{id}/cancel \
  -H "Authorization: Bearer <token>"
```

---

## 🎣 Webhooks

Configure your Webhook URL in the Meta App Dashboard to receive real-time updates:
`https://your-domain.com/webhooks`

### Supported Events
- `messages`: Incoming text, media, etc.
- `message_status`: Sent, Delivered, Read.
- `template_status`: Approved, Rejected.
