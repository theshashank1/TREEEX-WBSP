# 🗄️ Database Schema

This document details the database schema for TREEEX-WBSP (PostgreSQL).

## 📊 Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    User ||--o{ Workspace : owns
    User ||--o{ WorkspaceMember : membership

    Workspace ||--o{ WorkspaceMember : has
    Workspace ||--o{ PhoneNumber : has
    Workspace ||--o{ Contact : has
    Workspace ||--o{ Conversation : has
    Workspace ||--o{ MediaFile : stores
    Workspace ||--o{ Template : manages
    Workspace ||--o{ Campaign : runs

    PhoneNumber ||--o{ Conversation : participates
    PhoneNumber ||--o{ Message : sends/receives
    PhoneNumber ||--o{ Template : registers
    PhoneNumber ||--o{ Campaign : sends

    Contact ||--o{ Conversation : participates
    Contact ||--o{ CampaignMessage : receives

    Conversation ||--o{ Message : contains

    Campaign ||--o{ CampaignMessage : generates
    Message ||--o{ CampaignMessage : tracks
    Message ||--o| MediaFile : attachments
```

---

## 🏗️ Tables Reference

### Access Management (`server.models.access`)

#### `users`
Global user registry (synced with Supabase Auth).
- `id` (UUID, PK)
- `email` (String, Unique)
- `name` (String)

#### `workspaces`
Tenant isolation unit.
- `id` (UUID, PK)
- `slug` (String, Unique)
- `api_key` (UUID, Unique)
- `webhook_secret` (UUID)
- `settings` (JSONB): Custom config

#### `workspace_members`
Links Users to Workspaces with roles.
- `role` (Enum): `OWNER`, `ADMIN`, `MEMBER`

### Messaging (`server.models.messaging`)

#### `conversations`
Support windows and threads.
- `status` (Enum): `OPEN`, `CLOSED`, `EXPIRED`
- `window_expires_at` (DateTime): 24h Meta window
- `last_message_at` (DateTime)

#### `messages`
Individual message records.
- `wa_message_id` (String): Meta Message ID
- `direction` (Enum): `INBOUND`, `OUTBOUND`
- `type` (Enum): `text`, `image`, `template`, etc.
- `content` (JSONB): Full message payload
- `status` (Enum): `sent`, `delivered`, `read`, `failed`

#### `media_files`
Metadata for files in Azure Blob Storage.
- `storage_url` (String): Path in storage
- `mime_type` (String)

### Marketing (`server.models.marketing`)

#### `templates`
WhatsApp Message Templates.
- `category` (Enum): `MARKETING`, `UTILITY`, `AUTHENTICATION`
- `status` (Enum): `APPROVED`, `REJECTED`, `PENDING`
- `components` (JSONB): Template structure

#### `campaigns`
Bulk broadcast jobs.
- `status` (Enum): `DRAFT`, `SCHEDULED`, `RUNNING`, `COMPLETED`
- `total_contacts`, `sent_count`, `failed_count` (Aggregates)

#### `campaign_messages`
Status tracking for individual campaign messages.
- Links `Campaign` + `Contact` + `Message`

### Contacts (`server.models.contacts`)

#### `phone_numbers`
Connected WhatsApp Business Accounts.
- `phone_number_id` (String): Meta Phone ID
- `access_token` (Text): System User Token

#### `contacts`
Customer database.
- `wa_id` (String): WhatsApp ID (usually phone number)
- `opted_in` (Boolean): Consent status
- `tags` (Array): Segmentation labels
