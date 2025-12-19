# TREEEX WhatsApp Business API Reference

> **Complete API Documentation** | Version 1.0 | Base URL: `https://destined-severely-serval.ngrok-free.app` (Local: `http://localhost:8000`)

---

## Table of Contents

- [Getting Started](#getting-started)
- [Authentication](#authentication)
- [Workspaces](#workspaces)
- [Phone Numbers](#phone-numbers)
- [Messages](#messages)
- [Media](#media)
- [Templates](#templates)
- [Contacts](#contacts)
- [Campaigns](#campaigns)
- [Webhooks](#webhooks)
- [Error Handling](#error-handling)

---

## Getting Started

### Base URLs

- **Public API:** `https://destined-severely-serval.ngrok-free.app`
- **Local API:** `http://localhost:8000`

### Authentication

Most endpoints require a Bearer token in the Authorization header:

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

Get your access token by signing up and signing in through the authentication endpoints.

### Common Response Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `201` | Created successfully |
| `204` | Success with no content |
| `400` | Bad request - check your parameters |
| `401` | Unauthorized - invalid or missing token |
| `403` | Forbidden - insufficient permissions |
| `404` | Resource not found |
| `422` | Validation error |
| `500` | Server error |

---

## Authentication

Manage user authentication and sessions.

### Sign Up

Create a new user account.

**Endpoint:** `POST /api/auth/signup`

**Authentication:** Not required

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "name": "John Doe"  // optional
}
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `provider` | string | `Email` | Authentication provider (Email, Google, GitHub) |

**Response:** `200 OK`

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "John Doe",
  "email": "user@example.com"
}
```

**Example:**

```bash
curl -X POST https://destined-severely-serval.ngrok-free.app/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "name": "John Doe"
  }'
```

---

### Sign In

Authenticate and receive an access token.

**Endpoint:** `POST /api/auth/signin`

**Authentication:** Not required

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `provider` | string | `Email` | Authentication provider |

**Response:** `200 OK`

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Example:**

```bash
curl -X POST https://destined-severely-serval.ngrok-free.app/api/auth/signin \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }'
```

---

### Refresh Token

Refresh your access token.

**Endpoint:** `POST /api/auth/refresh`

**Authentication:** Required

**Response:** `200 OK`

```json
{
  "access_token": "new_token_here",
  "refresh_token": "new_refresh_token_here"
}
```

---

### Get Current User

Get information about the currently authenticated user.

**Endpoint:** `GET /api/auth/me`

**Authentication:** Required

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "John Doe",
  "email_verified": true
}
```

---

## Workspaces

Manage workspaces and team members.

### Create Workspace

Create a new workspace for your team.

**Endpoint:** `POST /api/workspaces`

**Authentication:** Required

**Request Body:**

```json
{
  "name": "My Company",
  "plan": "free"  // free, pro, or enterprise
}
```

**Response:** `201 Created`

```json
{
  "id": "workspace-uuid",
  "name": "My Company",
  "slug": "my-company",
  "api_key": "wsk_...",
  "webhook_secret": "whsec_...",
  "created_by": "user-uuid",
  "plan": "free",
  "status": "active",
  "settings": {},
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://destined-severely-serval.ngrok-free.app/api/workspaces \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Company",
    "plan": "free"
  }'
```

---

### List Workspaces

Get all workspaces you're a member of.

**Endpoint:** `GET /api/workspaces`

**Authentication:** Required

**Response:** `200 OK`

```json
[
  {
    "id": "workspace-uuid",
    "name": "My Company",
    "slug": "my-company",
    "plan": "free",
    "status": "active",
    "created_at": "2024-01-01T00:00:00Z",
    "user_role": "OWNER"
  }
]
```

---

### Get Workspace

Get details of a specific workspace.

**Endpoint:** `GET /api/workspaces/{workspace_id}`

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `workspace_id` | UUID | Workspace ID |

**Response:** `200 OK`

Returns full workspace details including API key and webhook secret.

---

### Update Workspace

Update workspace settings.

**Endpoint:** `PATCH /api/workspaces/{workspace_id}`

**Authentication:** Required (OWNER or ADMIN role)

**Request Body:**

```json
{
  "name": "Updated Company Name",
  "plan": "pro",
  "status": "active",
  "settings": {
    "feature_flags": {}
  }
}
```

All fields are optional.

**Response:** `200 OK`

---

### Delete Workspace

Soft delete a workspace.

**Endpoint:** `DELETE /api/workspaces/{workspace_id}`

**Authentication:** Required (OWNER role only)

**Response:** `204 No Content`

---

### List Workspace Members

Get all members of a workspace.

**Endpoint:** `GET /api/workspaces/{workspace_id}/members`

**Authentication:** Required

**Response:** `200 OK`

```json
[
  {
    "id": "member-uuid",
    "user_id": "user-uuid",
    "role": "OWNER",
    "status": "active",
    "joined_at": "2024-01-01T00:00:00Z"
  }
]
```

**Roles:**
- `OWNER` - Full control
- `ADMIN` - Manage resources and members
- `MEMBER` - Read and send messages
- `AGENT` - Customer support access

---

### Add Workspace Member

Invite a user to your workspace.

**Endpoint:** `POST /api/workspaces/{workspace_id}/members`

**Authentication:** Required (OWNER or ADMIN role)

**Request Body:**

```json
{
  "user_email": "newmember@example.com",
  "role": "MEMBER"  // OWNER, ADMIN, MEMBER, or AGENT
}
```

**Response:** `200 OK`

---

## Phone Numbers

Register and manage WhatsApp Business phone numbers.

### Register Phone Number

Add a WhatsApp Business phone number to your workspace.

**Endpoint:** `POST /api/phone-numbers`

**Authentication:** Required (OWNER or ADMIN role)

**Request Body:**

```json
{
  "workspace_id": "workspace-uuid",
  "phone_number_id": "1234567890",  // Meta's Phone Number ID
  "access_token": "EAAxxxxxxxxx",    // Meta access token
  "display_name": "Customer Support",  // optional
  "business_id": "business-account-id"  // optional WABA ID
}
```

**Response:** `201 Created`

```json
{
  "id": "phone-uuid",
  "workspace_id": "workspace-uuid",
  "phone_number": "+1234567890",
  "phone_number_id": "1234567890",
  "display_name": "Customer Support",
  "business_id": "business-account-id",
  "quality_rating": "GREEN",
  "message_limit": 1000,
  "tier": "STANDARD",
  "status": "active",
  "verified_at": "2024-01-01T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Quality Ratings:**
- `GREEN` - Good quality, full limits
- `YELLOW` - Medium quality, reduced limits
- `RED` - Poor quality, severely limited
- `UNKNOWN` - Not yet rated

**Example:**

```bash
curl -X POST https://destined-severely-serval.ngrok-free.app/api/phone-numbers \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "workspace-uuid",
    "phone_number_id": "1234567890",
    "access_token": "EAAxxxxxxxxx",
    "display_name": "Customer Support"
  }'
```

---

### List Phone Numbers

Get all phone numbers in a workspace.

**Endpoint:** `GET /api/phone-numbers`

**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workspace_id` | UUID | Yes | Workspace ID |
| `status` | string | No | Filter by status (pending, active, disabled) |
| `limit` | integer | No | Results per page (1-100, default: 20) |
| `offset` | integer | No | Offset for pagination (default: 0) |

**Response:** `200 OK`

```json
{
  "data": [
    {
      "id": "phone-uuid",
      "workspace_id": "workspace-uuid",
      "phone_number": "+1234567890",
      "display_name": "Customer Support",
      "quality_rating": "GREEN",
      "message_limit": 1000,
      "status": "active"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

---

### Get Phone Number

Get details of a specific phone number.

**Endpoint:** `GET /api/phone-numbers/{phone_number_id}`

**Authentication:** Required

**Response:** `200 OK`

---

### Update Phone Number

Update phone number settings.

**Endpoint:** `PATCH /api/phone-numbers/{phone_number_id}`

**Authentication:** Required (OWNER or ADMIN role)

**Request Body:**

```json
{
  "display_name": "Sales Team",
  "access_token": "new_token",  // optional, will be validated
  "status": "active"  // pending, active, or disabled
}
```

All fields are optional.

**Response:** `200 OK`

---

### Delete Phone Number

Soft delete a phone number.

**Endpoint:** `DELETE /api/phone-numbers/{phone_number_id}`

**Authentication:** Required (OWNER or ADMIN role)

**Response:** `204 No Content`

---

### Sync Phone Number

Sync quality rating and message limits from Meta.

**Endpoint:** `POST /api/phone-numbers/{phone_number_id}/sync`

**Authentication:** Required

**Response:** `200 OK`

```json
{
  "id": "phone-uuid",
  "synced_at": "2024-01-01T00:00:00Z",
  "phone_number": "+1234567890",
  "quality_rating": "GREEN",
  "message_limit": 1000,
  "tier": "STANDARD",
  "status": "active"
}
```

**Example:**

```bash
curl -X POST https://destined-severely-serval.ngrok-free.app/api/phone-numbers/{phone_id}/sync \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### Exchange Token

Convert short-lived access token to long-lived token.

**Endpoint:** `POST /api/phone-numbers/{phone_number_id}/exchange-token`

**Authentication:** Required (OWNER or ADMIN role)

**Response:** `200 OK`

Returns updated phone number with new long-lived token (typically 60 days vs 1 hour).

> **Note:** System user tokens are already long-lived and don't need exchange.

---

## Messages

Send WhatsApp messages and track their status.

### Send Text Message

Send a simple text message.

**Endpoint:** `POST /api/messages/send/text`

**Authentication:** Required

**Request Body:**

```json
{
  "workspace_id": "workspace-uuid",
  "phone_number_id": "phone-uuid",
  "to": "+1234567890",  // E.164 format
  "text": "Hello! Thanks for contacting us."
}
```

**Response:** `201 Created`

```json
{
  "id": "message-uuid",
  "workspace_id": "workspace-uuid",
  "phone_number_id": "phone-uuid",
  "wa_message_id": "wamid.xxxxx",
  "direction": "outbound",
  "from_number": "+0987654321",
  "to_number": "+1234567890",
  "type": "text",
  "status": "queued"
}
```

**Message Statuses:**
- `queued` - In queue, not yet sent
- `sending` - Being sent to Meta
- `sent` - Accepted by Meta
- `delivered` - Delivered to recipient's device
- `read` - Opened by recipient
- `failed` - Delivery failed

**Example:**

```bash
curl -X POST https://destined-severely-serval.ngrok-free.app/api/messages/send/text \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "workspace-uuid",
    "phone_number_id": "phone-uuid",
    "to": "+1234567890",
    "text": "Hello! Thanks for contacting us."
  }'
```

---

### Send Template Message

Send a pre-approved WhatsApp template message.

**Endpoint:** `POST /api/messages/send/template`

**Authentication:** Required

**Request Body:**

```json
{
  "workspace_id": "workspace-uuid",
  "phone_number_id": "phone-uuid",
  "to": "+1234567890",
  "template_name": "welcome_message",
  "template_language": "en",
  "components": {
    "body": [
      {
        "type": "text",
        "text": "John"
      }
    ]
  }
}
```

**Response:** `201 Created`

---

### Send Media Message

Send an image, video, audio file, or document.

**Endpoint:** `POST /api/messages/send/media`

**Authentication:** Required

**Request Body:**

```json
{
  "workspace_id": "workspace-uuid",
  "phone_number_id": "phone-uuid",
  "to": "+1234567890",
  "media_type": "image",  // image, video, audio, or document
  "media_id": "media-uuid",  // from /api/media upload
  "caption": "Check out this image!"  // optional, max 3000 chars
}
```

**Media Types:**
- `image` - JPEG, PNG, GIF, BMP (max 16 MB)
- `video` - MP4, 3GPP, QuickTime (max 100 MB)
- `audio` - AAC, MP4, MPEG, AMR, OGG (max 16 MB)
- `document` - PDF, DOC, XLS, PPT, TXT (max 100 MB)

**Response:** `201 Created`

```json
{
  "id": "message-uuid",
  "workspace_id": "workspace-uuid",
  "phone_number_id": "phone-uuid",
  "to_number": "+1234567890",
  "type": "image",
  "status": "queued",
  "media_id": "media-uuid",
  "queued": true
}
```

**Example:**

```bash
# First upload the media (see Media section)
# Then send the message

curl -X POST https://destined-severely-serval.ngrok-free.app/api/messages/send/media \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "workspace-uuid",
    "phone_number_id": "phone-uuid",
    "to": "+1234567890",
    "media_type": "image",
    "media_id": "media-uuid",
    "caption": "Check this out!"
  }'
```

---

### Get Message Status

Check the delivery status of a message.

**Endpoint:** `GET /api/messages/{message_id}/status`

**Authentication:** Required

**Response:** `200 OK`

```json
{
  "id": "message-uuid",
  "wa_message_id": "wamid.xxxxx",
  "status": "delivered",
  "delivered_at": "2024-01-01T00:05:00Z",
  "read_at": "2024-01-01T00:10:00Z"
}
```

---

## Media

Upload and manage media files for WhatsApp messages.

### Upload Media

Upload a file to Azure Blob Storage.

**Endpoint:** `POST /api/media`

**Authentication:** Required

**Content-Type:** `multipart/form-data`

**Form Data:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `workspace_id` | UUID | Yes | Workspace ID |
| `file` | File | Yes | File to upload |

**File Size Limits:**
- Images: 16 MB
- Videos: 100 MB
- Audio: 16 MB
- Documents: 100 MB

**Response:** `201 Created`

```json
{
  "id": "media-uuid",
  "workspace_id": "workspace-uuid",
  "type": "image",
  "original_url": null,
  "storage_url": "https://storage.blob.core.windows.net/...",
  "file_name": "photo.jpg",
  "file_size": 1024000,
  "mime_type": "image/jpeg",
  "uploaded_by": "user-uuid",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://destined-severely-serval.ngrok-free.app/api/media \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "workspace_id=workspace-uuid" \
  -F "file=@/path/to/image.jpg"
```

**JavaScript Example:**

```javascript
const formData = new FormData();
formData.append('workspace_id', 'workspace-uuid');
formData.append('file', fileInput.files[0]);

const response = await fetch('https://destined-severely-serval.ngrok-free.app/api/media', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_ACCESS_TOKEN'
  },
  body: formData
});
```

---

### List Media

Get all media files in a workspace.

**Endpoint:** `GET /api/media`

**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workspace_id` | UUID | Yes | Workspace ID |
| `type` | string | No | Filter by type (image, video, audio, document) |
| `limit` | integer | No | Results per page (1-100, default: 20) |
| `offset` | integer | No | Offset for pagination |

**Response:** `200 OK`

```json
{
  "data": [
    {
      "id": "media-uuid",
      "workspace_id": "workspace-uuid",
      "type": "image",
      "file_name": "photo.jpg",
      "file_size": 1024000,
      "mime_type": "image/jpeg",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

---

### Get Media Details

Get information about a specific media file.

**Endpoint:** `GET /api/media/{media_id}`

**Authentication:** Required

**Response:** `200 OK`

---

### Delete Media

Soft delete a media file.

**Endpoint:** `DELETE /api/media/{media_id}`

**Authentication:** Required

**Response:** `204 No Content`

---

### Download Media

Download a media file (307 redirect to Azure SAS URL).

**Endpoint:** `GET /api/media/{media_id}/download`

**Authentication:** Required

**Response:** `307 Temporary Redirect`

Redirects to a temporary Azure SAS URL (valid for 60 minutes).

**Example:**

```bash
curl -L https://destined-severely-serval.ngrok-free.app/api/media/{media_id}/download \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -O
```

---

### Get Media URL

Get a temporary signed URL for a media file.

**Endpoint:** `GET /api/media/{media_id}/url`

**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `expiry_minutes` | integer | 60 | URL validity in minutes (5-1440) |

**Response:** `200 OK`

```json
{
  "url": "https://storage.blob.core.windows.net/...?sas-token",
  "expires_in_minutes": 60,
  "expires_at": "2024-01-01T01:00:00Z"
}
```

**Example:**

```bash
curl https://destined-severely-serval.ngrok-free.app/api/media/{media_id}/url?expiry_minutes=120 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Templates

Create and manage WhatsApp message templates.

### Create Template

Create a new WhatsApp message template.

**Endpoint:** `POST /api/templates`

**Authentication:** Required

**Request Body:**

```json
{
  "workspace_id": "workspace-uuid",
  "phone_number_id": "phone-uuid",
  "name": "welcome_message",  // lowercase, no spaces
  "category": "MARKETING",  // MARKETING, UTILITY, or AUTHENTICATION
  "language": "en",
  "components": {
    "body": {
      "text": "Hello {{1}}, welcome to our service!"
    },
    "footer": {
      "text": "Reply STOP to unsubscribe"
    }
  }
}
```

**Template Categories:**
- `MARKETING` - Promotional messages
- `UTILITY` - Account updates, order status
- `AUTHENTICATION` - OTP and verification codes

**Response:** `201 Created`

```json
{
  "id": "template-uuid",
  "workspace_id": "workspace-uuid",
  "phone_number_id": "phone-uuid",
  "name": "welcome_message",
  "category": "MARKETING",
  "language": "en",
  "status": "PENDING",  // PENDING, APPROVED, REJECTED
  "meta_template_id": null,
  "components": {...},
  "rejection_reason": null,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

> **Note:** Templates must be approved by Meta before use. This typically takes 24-48 hours.

---

### List Templates

Get all templates in a workspace.

**Endpoint:** `GET /api/templates`

**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workspace_id` | UUID | Yes | Workspace ID |
| `phone_number_id` | UUID | No | Filter by phone number |
| `status` | string | No | Filter by status (PENDING, APPROVED, REJECTED) |
| `category` | string | No | Filter by category |
| `limit` | integer | No | Results per page (1-100, default: 20) |
| `offset` | integer | No | Offset for pagination |

**Response:** `200 OK`

```json
{
  "data": [
    {
      "id": "template-uuid",
      "name": "welcome_message",
      "category": "MARKETING",
      "language": "en",
      "status": "APPROVED"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

---

### Get Template

Get details of a specific template.

**Endpoint:** `GET /api/templates/{template_id}`

**Authentication:** Required

**Response:** `200 OK`

---

### Update Template

Update a template's components or status.

**Endpoint:** `PATCH /api/templates/{template_id}`

**Authentication:** Required

**Request Body:**

```json
{
  "components": {...},
  "status": "APPROVED"
}
```

All fields are optional.

**Response:** `200 OK`

---

### Delete Template

Soft delete a template.

**Endpoint:** `DELETE /api/templates/{template_id}`

**Authentication:** Required

**Response:** `204 No Content`

---

## Contacts

Manage your contact list.

### Create Contact

Add a new contact to your workspace.

**Endpoint:** `POST /api/contacts`

**Authentication:** Required

**Request Body:**

```json
{
  "workspace_id": "workspace-uuid",
  "phone_number": "+1234567890",  // E.164 format required
  "name": "John Doe",  // optional
  "tags": ["customer", "vip"]  // optional
}
```

**Response:** `201 Created`

```json
{
  "id": "contact-uuid",
  "workspace_id": "workspace-uuid",
  "wa_id": "1234567890",
  "phone_number": "+1234567890",
  "name": "John Doe",
  "opted_in": true,
  "tags": ["customer", "vip"],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://destined-severely-serval.ngrok-free.app/api/contacts \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "workspace-uuid",
    "phone_number": "+1234567890",
    "name": "John Doe",
    "tags": ["customer"]
  }'
```

---

### List Contacts

Get all contacts in a workspace.

**Endpoint:** `GET /api/contacts`

**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workspace_id` | UUID | Yes | Workspace ID |
| `tags` | string | No | Filter by tags (comma-separated) |
| `opted_in` | boolean | No | Filter by opt-in status |
| `search` | string | No | Search by name or phone number |
| `limit` | integer | No | Results per page (1-100, default: 20) |
| `offset` | integer | No | Offset for pagination |

**Response:** `200 OK`

```json
{
  "data": [
    {
      "id": "contact-uuid",
      "workspace_id": "workspace-uuid",
      "phone_number": "+1234567890",
      "name": "John Doe",
      "opted_in": true,
      "tags": ["customer", "vip"]
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

**Example:**

```bash
# Search for contacts
curl "https://destined-severely-serval.ngrok-free.app/api/contacts?workspace_id=workspace-uuid&search=John" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Filter by tags
curl "https://destined-severely-serval.ngrok-free.app/api/contacts?workspace_id=workspace-uuid&tags=vip,customer" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### Get Contact

Get details of a specific contact.

**Endpoint:** `GET /api/contacts/{contact_id}`

**Authentication:** Required

**Response:** `200 OK`

---

### Update Contact

Update contact information.

**Endpoint:** `PATCH /api/contacts/{contact_id}`

**Authentication:** Required

**Request Body:**

```json
{
  "name": "Jane Doe",
  "tags": ["customer", "premium"],
  "opted_in": true
}
```

All fields are optional.

**Response:** `200 OK`

---

### Delete Contact

Soft delete a contact.

**Endpoint:** `DELETE /api/contacts/{contact_id}`

**Authentication:** Required

**Response:** `204 No Content`

---

### Import Contacts

Bulk import contacts from CSV or Excel file.

**Endpoint:** `POST /api/contacts/import`

**Authentication:** Required

**Content-Type:** `multipart/form-data`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workspace_id` | UUID | Yes | Workspace ID |

**Form Data:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | Yes | CSV or Excel file |

**Expected CSV Columns:**
- `phone` (required) - Phone number in E.164 format or common formats
- `name` (optional) - Contact name
- `labels` or `tags` (optional) - Comma or semicolon separated tags

**CSV Example:**

```csv
phone,name,tags
+1234567890,John Doe,customer;vip
+0987654321,Jane Smith,customer
1234567890,Bob Johnson,prospect
```

**Response:** `200 OK`

```json
{
  "total_rows": 3,
  "imported": 2,
  "updated": 1,
  "failed": 0,
  "results": [
    {
      "row_number": 1,
      "phone_number": "+1234567890",
      "status": "imported",
      "reason": null
    },
    {
      "row_number": 2,
      "phone_number": "+0987654321",
      "status": "updated",
      "reason": null
    },
    {
      "row_number": 3,
      "phone_number": "1234567890",
      "status": "failed",
      "reason": "Invalid phone number format"
    }
  ]
}
```

**Example:**

```bash
curl -X POST "https://destined-severely-serval.ngrok-free.app/api/contacts/import?workspace_id=workspace-uuid" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@contacts.csv"
```

---

## Campaigns

Create and manage message campaigns.

### Create Campaign

Create a new message campaign.

**Endpoint:** `POST /api/campaigns`

**Authentication:** Required

**Request Body:**

```json
{
  "workspace_id": "workspace-uuid",
  "phone_number_id": "phone-uuid",
  "template_id": "template-uuid",  // optional
  "name": "Summer Sale 2024"
}
```

**Response:** `201 Created`

```json
{
  "id": "campaign-uuid",
  "workspace_id": "workspace-uuid",
  "phone_number_id": "phone-uuid",
  "template_id": "template-uuid",
  "name": "Summer Sale 2024",
  "total_contacts": 0,
  "sent_count": 0,
  "delivered_count": 0,
  "read_count": 0,
  "failed_count": 0,
  "status": "draft"
}
```

**Campaign Statuses:**
- `draft` - Being configured
- `scheduled` - Scheduled for future or paused
- `sending` - Currently sending messages
- `completed` - All messages sent
- `failed` - Campaign failed

---

### List Campaigns

Get all campaigns in a workspace.

**Endpoint:** `GET /api/campaigns`

**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workspace_id` | UUID | Yes | Workspace ID |
| `status` | string | No | Filter by status |
| `limit` | integer | No | Results per page (1-100, default: 20) |
| `offset` | integer | No | Offset for pagination |

**Response:** `200 OK`

```json
{
  "data": [
    {
      "id": "campaign-uuid",
      "name": "Summer Sale 2024",
      "status": "sending",
      "total_contacts": 1000,
      "sent_count": 500,
      "delivered_count": 450,
      "read_count": 200
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

---

### Get Campaign

Get details of a specific campaign.

**Endpoint:** `GET /api/campaigns/{campaign_id}`

**Authentication:** Required

**Response:** `200 OK`

---

### Update Campaign

Update campaign details.

**Endpoint:** `PATCH /api/campaigns/{campaign_id}`

**Authentication:** Required

**Request Body:**

```json
{
  "name": "Updated Campaign Name",
  "status": "scheduled"
}
```

All fields are optional.

**Response:** `200 OK`

---

### Delete Campaign

Soft delete a campaign.

**Endpoint:** `DELETE /api/campaigns/{campaign_id}`

**Authentication:** Required

**Response:** `204 No Content`

---

### Start Campaign

Start sending messages for a campaign.

**Endpoint:** `POST /api/campaigns/{campaign_id}/start`

**Authentication:** Required

**Response:** `200 OK`

Changes status from `draft` or `scheduled` to `sending`.

**Example:**

```bash
curl -X POST https://destined-severely-serval.ngrok-free.app/api/campaigns/{campaign_id}/start \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### Pause Campaign

Pause an active campaign.

**Endpoint:** `POST /api/campaigns/{campaign_id}/pause`

**Authentication:** Required

**Response:** `200 OK`

Changes status from `sending` to `scheduled` (paused state).

---

## Webhooks

Receive WhatsApp events from Meta.

### Verify Webhook

Webhook verification endpoint for Meta setup.

**Endpoint:** `GET /webhook`

**Authentication:** Not required (Meta verification token used)

**Description:** Meta calls this once when you first configure the webhook to verify ownership.

---

### Receive Webhook

Main webhook endpoint for receiving all Meta events.

**Endpoint:** `POST /webhook`

**Authentication:** HMAC signature verification

**Headers:**

| Header | Description |
|--------|-------------|
| `X-Hub-Signature-256` | HMAC-SHA256 signature for verification |

**Flow:**
1. Receives raw body from Meta
2. Verifies HMAC signature
3. Parses JSON payload
4. Checks idempotency (skips duplicates)
5. Routes event to Redis queue by type
6. Returns 200 OK immediately

**Event Types:**
- Message status updates (sent, delivered, read, failed)
- Incoming messages
- Template status changes
- Phone number quality updates

**Example Payload (Message Status):**

```json
{
  "entry": [
    {
      "changes": [
        {
          "value": {
            "statuses": [
              {
                "id": "wamid.xxxxx",
                "status": "delivered",
                "timestamp": "1234567890"
              }
            ]
          }
        }
      ]
    }
  ]
}
```

> **Note:** This endpoint is public but secured with HMAC signature verification. Configure your webhook URL and secret in Meta Business Suite.

---

## Error Handling

### Error Response Format

All errors follow a consistent JSON structure:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "Invalid email format",
      "type": "value_error"
    }
  ]
}
```

For simple errors:

```json
{
  "detail": "Resource not found"
}
```

### Common Error Scenarios

#### Authentication Errors

**401 Unauthorized**
```json
{
  "detail": "Invalid credentials"
}
```

**Solution:** Check your email/password or provide a valid access token.

---

**403 Forbidden**
```json
{
  "detail": "Insufficient permissions. OWNER or ADMIN role required"
}
```

**Solution:** Contact workspace owner to upgrade your role.

---

#### Validation Errors

**422 Unprocessable Entity**
```json
{
  "detail": [
    {
      "loc": ["body", "phone_number"],
      "msg": "Phone number must be in E.164 format",
      "type": "value_error"
    }
  ]
}
```

**Solution:** Fix the validation error in your request.

---

#### Resource Errors

**404 Not Found**
```json
{
  "detail": "Workspace not found"
}
```

**Solution:** Verify the resource ID exists and you have access to it.

---

### Rate Limiting

Rate limits vary by workspace plan:

| Plan | Requests/Hour | Requests/Day |
|------|---------------|--------------|
| Free | 100 | 1,000 |
| Pro | 1,000 | 10,000 |
| Enterprise | Custom | Custom |

**429 Too Many Requests**
```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

**Solution:** Slow down your requests or upgrade your plan.

---

### Phone Number Formats

All phone numbers must be in E.164 format:

✅ **Correct:**
- `+1234567890`
- `+442012345678`

❌ **Incorrect:**
- `1234567890`
- `(123) 456-7890`
- `+1 234-567-8900`

---

## Best Practices

### 1. Error Handling

Always handle errors gracefully:

```javascript
try {
  const response = await fetch(url, options);
  if (!response.ok) {
    const error = await response.json();
    console.error('API Error:', error.detail);
  }
  const data = await response.json();
} catch (error) {
  console.error('Network Error:', error);
}
```

### 2. Token Management

- Store tokens securely (not in localStorage for sensitive apps)
- Implement token refresh logic
- Handle 401 errors by redirecting to login

### 3. Pagination

For large datasets, always use pagination:

```javascript
let offset = 0;
const limit = 100;
let allContacts = [];

while (true) {
  const response = await fetch(
    `${baseUrl}/api/contacts?workspace_id=${id}&limit=${limit}&offset=${offset}`
  );
  const data = await response.json();

  allContacts = allContacts.concat(data.data);

  if (data.data.length < limit) break;
  offset += limit;
}
```

### 4. File Uploads

Use FormData for file uploads:

```javascript
const formData = new FormData();
formData.append('workspace_id', workspaceId);
formData.append('file', fileInput.files[0]);

const response = await fetch(`${baseUrl}/api/media`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
    // Don't set Content-Type, browser will set it with boundary
  },
  body: formData
});
```

### 5. Phone Number Validation

Always validate phone numbers before API calls:

```javascript
function isValidE164(phone) {
  return /^\+[1-9]\d{1,14}$/.test(phone);
}
```

---

## Support

For questions or issues:
- Review the error message details
- Check your authentication and permissions
- Verify phone number formats
- Ensure workspace membership
- Contact backend team for support

---

**Last Updated:** 2025-12-19
**API Version:** 1.0
**Public URL:** `https://destined-severely-serval.ngrok-free.app`
**Local URL:** `http://localhost:8000`
