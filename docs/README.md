# API Documentation

This directory contains comprehensive documentation for the TREEEX WhatsApp Business API.

## 📚 Documentation Files

- **`API_REFERENCE.mdx`** - Complete API reference with code examples
- **`openapi.json`** - OpenAPI 3.1 specification (machine-readable)
- **`generate_docs.py`** - Script to regenerate documentation from OpenAPI spec

## 🚀 Quick Start

### Base URL
```
http://localhost:8000
```

### Authentication
Most endpoints require Bearer token authentication:
```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Getting Started

1. **Sign Up**: Create an account at `POST /api/auth/signup`
2. **Sign In**: Get your access token at `POST /api/auth/signin`
3. **Create Workspace**: Set up your workspace at `POST /api/workspaces`
4. **Register Phone Number**: Add your WhatsApp Business number at `POST /api/phone-numbers`
5. **Start Sending**: Use the messaging endpoints to send messages

## 📖 API Overview

### Authentication Endpoints
- `POST /api/auth/signup` - Create a new account
- `POST /api/auth/signin` - Login and get access token
- `POST /api/auth/refresh` - Refresh your access token
- `GET /api/auth/me` - Get current user info

### Workspace Management
- Manage workspaces and team members
- Handle workspace settings and permissions
- Supports multiple workspaces per user

### Phone Numbers
- Register WhatsApp Business phone numbers
- Sync quality ratings and message limits from Meta
- Exchange tokens for long-lived access

### Campaigns
- Create and manage message campaigns
- Track delivery, read, and failure metrics
- Start/pause campaign execution

### Messages
- Send text, media, and template messages
- Track message delivery status
- Support for rich media (images, videos, documents, audio)

### Media
- Upload media files to Azure Blob Storage
- Generate temporary signed URLs
- Download media files

### Templates
- Create WhatsApp message templates
- Manage template approval status
- Support for MARKETING, UTILITY, and AUTHENTICATION categories

### Contacts
- Manage contact lists
- Import contacts from CSV/Excel
- Tag and segment contacts
- Track opt-in status

### Webhooks
- Receive WhatsApp events from Meta
- Automatic signature verification
- Event routing to Redis queues

## 🔄 Updating Documentation

To regenerate the documentation after API changes:

```bash
# The server must be running to fetch the latest OpenAPI spec
python run.py

# In another terminal, generate docs
python docs/generate_docs.py
```

## 📝 Code Examples

### Authentication Example (JavaScript)

```javascript
// Sign Up
const signupResponse = await fetch('http://localhost:8000/api/auth/signup', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'developer@example.com',
    password: 'SecurePassword123!',
    name: 'John Doe'
  })
});

const signupData = await signupResponse.json();

// Sign In
const signinResponse = await fetch('http://localhost:8000/api/auth/signin', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'developer@example.com',
    password: 'SecurePassword123!'
  })
});

const { access_token } = await signinResponse.json();

// Use token for authenticated requests
const headers = {
  'Authorization': `Bearer ${access_token}`,
  'Content-Type': 'application/json'
};
```

### Send Text Message Example

```javascript
const response = await fetch('http://localhost:8000/api/messages/send/text', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_ACCESS_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    workspace_id: '550e8400-e29b-41d4-a716-446655440000',
    phone_number_id: '550e8400-e29b-41d4-a716-446655440000',
    to: '+1234567890',
    text: 'Hello from the API!'
  })
});

const data = await response.json();
```

### Upload Media Example

```javascript
const formData = new FormData();
formData.append('workspace_id', '550e8400-e29b-41d4-a716-446655440000');
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8000/api/media', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_ACCESS_TOKEN'
  },
  body: formData
});

const mediaData = await response.json();
```

## 🏗️ API Structure

```
/api
├── /auth              # Authentication & user management
├── /workspaces        # Workspace management
├── /phone-numbers     # WhatsApp Business phone numbers
├── /campaigns         # Message campaigns
├── /messages          # Send messages
├── /media             # Media file management
├── /templates         # WhatsApp templates
└── /contacts          # Contact management

/webhook               # WhatsApp webhook receiver
```

## 📊 Response Format

All API responses follow a consistent JSON structure:

### Success Response
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "success",
  "data": { ... }
}
```

### Error Response
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

## 🔐 Security

- All endpoints require HTTPS in production
- Bearer token authentication for protected routes
- Webhook signature verification using HMAC-SHA256
- Input validation on all endpoints
- Rate limiting (configured per workspace plan)

## 📞 Support

For questions or issues:
- Check the detailed API reference in `API_REFERENCE.mdx`
- Review the OpenAPI spec in `openapi.json`
- Contact the backend team

## 🛠️ Development

### Tech Stack
- **Framework**: FastAPI
- **Database**: Supabase (PostgreSQL)
- **Cache**: Redis
- **Storage**: Azure Blob Storage
- **Queue**: Redis Queue

### Pagination
List endpoints support pagination:
- `limit`: Results per page (default: 20, max: 100)
- `offset`: Number of items to skip

### Filtering
Most list endpoints support filtering:
- `workspace_id`: Filter by workspace
- `status`: Filter by status
- Additional filters per endpoint

## 📈 Rate Limits

Rate limits vary by workspace plan:
- **Free**: 100 requests/hour
- **Pro**: 1,000 requests/hour
- **Enterprise**: Custom limits

## 🌐 Interactive Documentation

You can also access interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json
