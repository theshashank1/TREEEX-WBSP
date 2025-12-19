# API Architecture Overview

## System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        FE[Frontend Application]
        Mobile[Mobile App]
        API_Client[Third-party Integrations]
    end

    subgraph "API Gateway"
        FastAPI[FastAPI Server<br/>Port 8000]
        Ngrok[Ngrok Tunnel<br/>Public URL]
    end

    subgraph "Authentication"
        Auth[Auth Module<br/>/api/auth/*]
        Supabase_Auth[Supabase Auth]
    end

    subgraph "Core Services"
        Workspaces[Workspace Service<br/>/api/workspaces/*]
        PhoneNumbers[Phone Number Service<br/>/api/phone-numbers/*]
        Messages[Message Service<br/>/api/messages/*]
        Media[Media Service<br/>/api/media/*]
        Templates[Template Service<br/>/api/templates/*]
        Contacts[Contact Service<br/>/api/contacts/*]
        Campaigns[Campaign Service<br/>/api/campaigns/*]
    end

    subgraph "External Services"
        Meta[Meta WhatsApp API]
        Azure[Azure Blob Storage]
        Webhook_Handler[Webhook Handler<br/>/webhook]
    end

    subgraph "Data Layer"
        Supabase[(Supabase<br/>PostgreSQL)]
        Redis[(Redis Cache<br/>& Queue)]
    end

    subgraph "Background Workers"
        Outbound[Outbound Message Worker]
        Status[Status Update Worker]
        Campaign_Worker[Campaign Worker]
    end

    FE --> FastAPI
    Mobile --> FastAPI
    API_Client --> FastAPI
    FastAPI --> Ngrok

    FastAPI --> Auth
    Auth --> Supabase_Auth

    FastAPI --> Workspaces
    FastAPI --> PhoneNumbers
    FastAPI --> Messages
    FastAPI --> Media
    FastAPI --> Templates
    FastAPI --> Contacts
    FastAPI --> Campaigns

    Workspaces --> Supabase
    PhoneNumbers --> Supabase
    Messages --> Supabase
    Messages --> Redis
    Media --> Supabase
    Media --> Azure
    Templates --> Supabase
    Contacts --> Supabase
    Campaigns --> Supabase

    Meta --> Webhook_Handler
    Webhook_Handler --> Redis

    Redis --> Outbound
    Redis --> Status
    Redis --> Campaign_Worker

    Outbound --> Meta
    Status --> Supabase
    Campaign_Worker --> Messages

    style FastAPI fill:#49CC90
    style Supabase fill:#3ECF8E
    style Redis fill:#DC382D
    style Meta fill:#25D366
    style Azure fill:#0078D4
```

## Request Flow

### 1. Authentication Flow

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant Supabase

    Client->>FastAPI: POST /api/auth/signup
    FastAPI->>Supabase: Create user
    Supabase-->>FastAPI: User created
    FastAPI-->>Client: User details

    Client->>FastAPI: POST /api/auth/signin
    FastAPI->>Supabase: Verify credentials
    Supabase-->>FastAPI: Access token
    FastAPI-->>Client: Access token + user info

    Client->>FastAPI: GET /api/auth/me<br/>[Authorization: Bearer token]
    FastAPI->>Supabase: Verify token
    Supabase-->>FastAPI: User info
    FastAPI-->>Client: User details
```

### 2. Send Message Flow

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant Database
    participant Redis
    participant Worker
    participant Meta

    Client->>FastAPI: POST /api/messages/send/text
    FastAPI->>Database: Verify workspace & phone number
    Database-->>FastAPI: Verified
    FastAPI->>Database: Create message record
    Database-->>FastAPI: Message created
    FastAPI->>Redis: Queue message
    Redis-->>FastAPI: Queued
    FastAPI-->>Client: Message queued (202)

    Worker->>Redis: Dequeue message
    Worker->>Meta: Send to WhatsApp API
    Meta-->>Worker: Message ID
    Worker->>Database: Update message status

    Meta->>FastAPI: Webhook: message delivered
    FastAPI->>Redis: Queue status update
    Worker->>Database: Update to 'delivered'
```

### 3. Media Upload & Send Flow

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant Database
    participant Azure
    participant Redis
    participant Meta

    Client->>FastAPI: POST /api/media (multipart)
    FastAPI->>Azure: Upload file
    Azure-->>FastAPI: Blob URL
    FastAPI->>Database: Create media record
    Database-->>FastAPI: Media ID
    FastAPI-->>Client: Media details + ID

    Client->>FastAPI: POST /api/messages/send/media
    FastAPI->>Database: Verify media exists
    FastAPI->>Azure: Generate SAS URL
    Azure-->>FastAPI: Temporary URL
    FastAPI->>Redis: Queue media message
    FastAPI-->>Client: Message queued

    Redis->>Meta: Send media message
    Meta-->>Redis: Delivered
```

### 4. Webhook Processing Flow

```mermaid
sequenceDiagram
    participant Meta
    participant FastAPI
    participant Redis
    participant Worker
    participant Database

    Meta->>FastAPI: POST /webhook<br/>[X-Hub-Signature-256]
    FastAPI->>FastAPI: Verify HMAC signature
    FastAPI->>FastAPI: Check idempotency
    FastAPI->>Redis: Route event to queue
    FastAPI-->>Meta: 200 OK

    Worker->>Redis: Dequeue event

    alt Message Status Update
        Worker->>Database: Update message status
    else Incoming Message
        Worker->>Database: Create message record
        Worker->>Database: Find/create contact
    else Template Status
        Worker->>Database: Update template status
    end
```

## Data Models

### Core Entities

```mermaid
erDiagram
    User ||--o{ WorkspaceMember : "belongs to"
    Workspace ||--o{ WorkspaceMember : "has"
    Workspace ||--o{ PhoneNumber : "has"
    Workspace ||--o{ Contact : "has"
    Workspace ||--o{ Campaign : "has"
    Workspace ||--o{ Media : "has"

    PhoneNumber ||--o{ Template : "has"
    PhoneNumber ||--o{ Message : "sends"
    PhoneNumber ||--o{ Campaign : "uses"

    Contact ||--o{ Message : "receives"
    Contact ||--o{ Conversation : "participates"

    Campaign ||--o{ CampaignContact : "targets"
    Campaign }o--|| Template : "uses"

    Template ||--o{ Message : "used in"

    Message }o--|| Conversation : "belongs to"
    Message }o--o| Media : "contains"

    User {
        uuid id PK
        string email
        string name
        timestamp created_at
    }

    Workspace {
        uuid id PK
        string name
        string slug
        uuid api_key
        string plan
        string status
    }

    WorkspaceMember {
        uuid id PK
        uuid user_id FK
        uuid workspace_id FK
        string role
        string status
    }

    PhoneNumber {
        uuid id PK
        uuid workspace_id FK
        string phone_number
        string phone_number_id
        string quality_rating
        integer message_limit
        string status
    }

    Contact {
        uuid id PK
        uuid workspace_id FK
        string wa_id
        string phone_number
        string name
        boolean opted_in
        array tags
    }

    Message {
        uuid id PK
        uuid workspace_id FK
        uuid phone_number_id FK
        uuid conversation_id FK
        string wa_message_id
        string direction
        string type
        string status
        jsonb content
    }

    Campaign {
        uuid id PK
        uuid workspace_id FK
        uuid phone_number_id FK
        uuid template_id FK
        string name
        string status
        integer total_contacts
        integer sent_count
    }

    Template {
        uuid id PK
        uuid phone_number_id FK
        string name
        string category
        string language
        string status
        jsonb components
    }

    Media {
        uuid id PK
        uuid workspace_id FK
        string type
        string storage_url
        string file_name
        integer file_size
        string mime_type
    }
```

## API Endpoint Structure

```
TREEEX WhatsApp Business API
│
├── /webhook (Public - No Auth)
│   ├── GET  - Webhook verification
│   └── POST - Receive Meta events
│
└── /api (Authenticated)
    │
    ├── /auth
    │   ├── POST /signup      - Create account
    │   ├── POST /signin      - Login
    │   ├── POST /refresh     - Refresh token
    │   └── GET  /me          - Current user
    │
    ├── /workspaces
    │   ├── GET    /                      - List workspaces
    │   ├── POST   /                      - Create workspace
    │   ├── GET    /{id}                  - Get workspace
    │   ├── PATCH  /{id}                  - Update workspace
    │   ├── DELETE /{id}                  - Delete workspace
    │   ├── GET    /{id}/members          - List members
    │   └── POST   /{id}/members          - Add member
    │
    ├── /phone-numbers
    │   ├── GET    /                      - List phone numbers
    │   ├── POST   /                      - Register phone number
    │   ├── GET    /{id}                  - Get phone number
    │   ├── PATCH  /{id}                  - Update phone number
    │   ├── DELETE /{id}                  - Delete phone number
    │   ├── POST   /{id}/sync             - Sync from Meta
    │   └── POST   /{id}/exchange-token   - Get long-lived token
    │
    ├── /messages
    │   ├── POST /send/text               - Send text message
    │   ├── POST /send/template           - Send template message
    │   ├── POST /send/media              - Send media message
    │   └── GET  /{id}/status             - Get message status
    │
    ├── /media
    │   ├── GET    /                      - List media files
    │   ├── POST   /                      - Upload media
    │   ├── GET    /{id}                  - Get media details
    │   ├── DELETE /{id}                  - Delete media
    │   ├── GET    /{id}/download         - Download media (redirect)
    │   └── GET    /{id}/url              - Get signed URL
    │
    ├── /templates
    │   ├── GET    /                      - List templates
    │   ├── POST   /                      - Create template
    │   ├── GET    /{id}                  - Get template
    │   ├── PATCH  /{id}                  - Update template
    │   └── DELETE /{id}                  - Delete template
    │
    ├── /contacts
    │   ├── GET    /                      - List contacts
    │   ├── POST   /                      - Create contact
    │   ├── GET    /{id}                  - Get contact
    │   ├── PATCH  /{id}                  - Update contact
    │   ├── DELETE /{id}                  - Delete contact
    │   └── POST   /import                - Import from CSV/Excel
    │
    └── /campaigns
        ├── GET    /                      - List campaigns
        ├── POST   /                      - Create campaign
        ├── GET    /{id}                  - Get campaign
        ├── PATCH  /{id}                  - Update campaign
        ├── DELETE /{id}                  - Delete campaign
        ├── POST   /{id}/start            - Start campaign
        └── POST   /{id}/pause            - Pause campaign
```

## Security & Permissions

### Role-Based Access Control (RBAC)

```mermaid
graph LR
    subgraph Roles
        OWNER[OWNER<br/>Full control]
        ADMIN[ADMIN<br/>Manage resources]
        MEMBER[MEMBER<br/>Read/Send messages]
        AGENT[AGENT<br/>Customer support]
    end

    subgraph Permissions
        P1[Delete Workspace]
        P2[Manage Members]
        P3[Manage Phone Numbers]
        P4[Send Messages]
        P5[View Analytics]
        P6[Manage Campaigns]
    end

    OWNER --> P1
    OWNER --> P2
    OWNER --> P3
    OWNER --> P4
    OWNER --> P5
    OWNER --> P6

    ADMIN --> P2
    ADMIN --> P3
    ADMIN --> P4
    ADMIN --> P5
    ADMIN --> P6

    MEMBER --> P4
    MEMBER --> P5

    AGENT --> P4

    style OWNER fill:#F93E3E
    style ADMIN fill:#FCA130
    style MEMBER fill:#49CC90
    style AGENT fill:#61AFFE
```

### Authentication Flow

1. **Sign Up** → Email + Password → User created in Supabase
2. **Sign In** → Email + Password → Access token (JWT)
3. **API Calls** → Bearer token in Authorization header
4. **Token Refresh** → POST /api/auth/refresh

## Message Status Lifecycle

```mermaid
stateDiagram-v2
    [*] --> queued: API Request
    queued --> sending: Worker picks up
    sending --> sent: Meta accepts
    sending --> failed: Meta rejects
    sent --> delivered: Meta delivers
    sent --> failed: Delivery fails
    delivered --> read: User reads
    delivered --> failed: Expires
    read --> [*]
    failed --> [*]

    note right of queued
        Message in Redis queue
    end note

    note right of sending
        Worker processing
    end note

    note right of sent
        Accepted by Meta
    end note

    note right of delivered
        Received on device
    end note

    note right of read
        Opened by recipient
    end note
```

## Campaign Workflow

```mermaid
stateDiagram-v2
    [*] --> draft: Create Campaign
    draft --> scheduled: Schedule
    draft --> sending: Start Now
    scheduled --> sending: Time Reached / Manual Start
    sending --> completed: All Sent
    sending --> paused: Pause
    sending --> failed: Error
    paused --> sending: Resume
    completed --> [*]
    failed --> [*]

    note right of draft
        Campaign being configured
    end note

    note right of scheduled
        Waiting for start time
    end note

    note right of sending
        Actively sending messages
    end note
```

## Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Server**: Uvicorn (ASGI)
- **Validation**: Pydantic
- **Tunneling**: Ngrok (for local development)

### Data & Storage
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth
- **Cache/Queue**: Redis
- **File Storage**: Azure Blob Storage

### External APIs
- **WhatsApp**: Meta Cloud API
- **Webhooks**: HMAC-SHA256 signature verification

### Background Processing
- **Queue**: Redis Queue (RQ)
- **Workers**: Python background workers

## Rate Limits & Quotas

### API Rate Limits (by Plan)

| Plan       | Requests/Hour | Requests/Day | Concurrent |
|------------|---------------|--------------|------------|
| Free       | 100           | 1,000        | 2          |
| Pro        | 1,000         | 10,000       | 10         |
| Enterprise | Custom        | Custom       | Custom     |

### WhatsApp Message Limits (by Quality Rating)

| Quality   | Tier      | Daily Limit     |
|-----------|-----------|-----------------|
| Green     | Standard  | 1,000           |
| Green     | Medium    | 10,000          |
| Green     | High      | 100,000         |
| Yellow    | Any       | Limited (50%)   |
| Red       | Any       | Severely Limited|

### File Upload Limits

| Media Type | Max Size | Formats                      |
|------------|----------|------------------------------|
| Image      | 16 MB    | JPEG, PNG, GIF, BMP          |
| Video      | 100 MB   | MP4, 3GPP, QuickTime         |
| Audio      | 16 MB    | AAC, MP4, MPEG, AMR, OGG    |
| Document   | 100 MB   | PDF, DOC, XLS, PPT, TXT     |

## Error Codes

| Code | Meaning              | Action                          |
|------|----------------------|---------------------------------|
| 200  | Success              | -                               |
| 201  | Created              | -                               |
| 204  | No Content           | -                               |
| 400  | Bad Request          | Check request parameters        |
| 401  | Unauthorized         | Provide valid access token      |
| 403  | Forbidden            | Check workspace permissions     |
| 404  | Not Found            | Resource doesn't exist          |
| 422  | Validation Error     | Fix request body/parameters     |
| 429  | Too Many Requests    | Slow down, check rate limits    |
| 500  | Server Error         | Contact support                 |

## Quick Reference

### Base URLs
- **Public API:** `https://destined-severely-serval.ngrok-free.app`
- **Local Development:** `http://localhost:8000`
- **Interactive Docs:** `http://localhost:8000/docs`
- **OpenAPI Spec:** `http://localhost:8000/openapi.json`

### Common Headers
```http
Content-Type: application/json
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Response Format
```json
{
  "id": "uuid",
  "field": "value",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Error Format
```json
{
  "detail": [
    {
      "loc": ["body", "field"],
      "msg": "error message",
      "type": "error_type"
    }
  ]
}
```
