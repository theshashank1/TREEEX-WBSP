---
title: "FastAPI"
description: "Complete API reference for FastAPI"
---

# FastAPI

> **Version:** 0.1.0

## Base URL

```
http://localhost:8000
```

## Authentication

Most endpoints require authentication using Bearer tokens.

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

## Table of Contents

- [Authentication](#authentication)
- [Campaigns](#campaigns)
- [Contacts](#contacts)
- [Media](#media)
- [Messages](#messages)
- [Phone Numbers](#phone-numbers)
- [Templates](#templates)
- [Webhooks](#webhooks)
- [Workspaces](#workspaces)
- [Data Schemas](#data-schemas)

## Authentication

### Signup

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#49CC90", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ POST }}</span>
  <code>/api/auth/signup</code>
</div>

#### Parameters

**Query Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `provider` | `Provider` | ❌ |  (default: `Email`) |


#### Request Body (`application/json`)

See schema: [`Signup`](#signup)

**Example:**

```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "name": "name"
}
```

#### Example Request

```bash
curl -X POST 'http://localhost:8000/api/auth/signup' \
  -H 'Content-Type: application/json' \
  -d '{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "name": "name"
}'
```

```javascript
const response = await fetch('http://localhost:8000/api/auth/signup', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: "user@example.com",
    password: "SecurePassword123!",
    name: "name"
  })
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`SignupResponse`](#signupresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Signin

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#49CC90", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ POST }}</span>
  <code>/api/auth/signin</code>
</div>

#### Parameters

**Query Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `provider` | `Provider` | ❌ |  (default: `Email`) |


#### Request Body (`application/json`)

See schema: [`Signup`](#signup)

**Example:**

```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "name": "name"
}
```

#### Example Request

```bash
curl -X POST 'http://localhost:8000/api/auth/signin' \
  -H 'Content-Type: application/json' \
  -d '{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "name": "name"
}'
```

```javascript
const response = await fetch('http://localhost:8000/api/auth/signin', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: "user@example.com",
    password: "SecurePassword123!",
    name: "name"
  })
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`SigninResponse`](#signinresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Refresh

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#49CC90", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ POST }}</span>
  <code>/api/auth/refresh</code>
</div>

#### Example Request

```bash
curl -X POST 'http://localhost:8000/api/auth/refresh'
```

```javascript
const response = await fetch('http://localhost:8000/api/auth/refresh', {
  method: 'POST',
});

const data = await response.json();
```

#### Responses

**200** - Successful Response



---


### Me

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#61AFFE", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ GET }}</span>
  <code>/api/auth/me</code>
</div>

#### Example Request

```bash
curl -X GET 'http://localhost:8000/api/auth/me'
```

```javascript
const response = await fetch('http://localhost:8000/api/auth/me', {
  method: 'GET',
});

const data = await response.json();
```

#### Responses

**200** - Successful Response



---


## Campaigns

### Create Campaign

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#49CC90", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ POST }}</span>
  <code>/api/campaigns</code>
</div>

Create a new campaign.

Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Request Body (`application/json`)

See schema: [`CampaignCreate`](#campaigncreate)

**Example:**

```json
{
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number_id": "550e8400-e29b-41d4-a716-446655440000",
  "template_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "name"
}
```

#### Example Request

```bash
curl -X POST 'http://localhost:8000/api/campaigns' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number_id": "550e8400-e29b-41d4-a716-446655440000",
  "template_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "name"
}'
```

```javascript
const response = await fetch('http://localhost:8000/api/campaigns', {
  method: 'POST',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    workspace_id: "550e8400-e29b-41d4-a716-446655440000",
    phone_number_id: "550e8400-e29b-41d4-a716-446655440000",
    template_id: "550e8400-e29b-41d4-a716-446655440000",
    name: "name"
  })
});

const data = await response.json();
```

#### Responses

**201** - Successful Response

Returns: [`CampaignResponse`](#campaignresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### List Campaigns

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#61AFFE", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ GET }}</span>
  <code>/api/campaigns</code>
</div>

List campaigns for a workspace.

Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Query Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ | Workspace ID to filter by |
| `status` | `any` | ❌ | Filter by status |
| `limit` | `integer` | ❌ |  (default: `20`) |
| `offset` | `integer` | ❌ |  (default: `0`) |


#### Example Request

```bash
curl -X GET 'http://localhost:8000/api/campaigns' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```javascript
const response = await fetch('http://localhost:8000/api/campaigns?workspace_id=550e8400-e29b-41d4-a716-446655440000', {
  method: 'GET',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN'
  }
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`CampaignListResponse`](#campaignlistresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Get Campaign

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#61AFFE", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ GET }}</span>
  <code>/api/campaigns/{campaign_id}</code>
</div>

Get campaign details.

Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `campaign_id` | `string (uuid)` | ✅ |  |


#### Example Request

```bash
curl -X GET 'http://localhost:8000/api/campaigns/550e8400-e29b-41d4-a716-446655440000' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```javascript
const response = await fetch('http://localhost:8000/api/campaigns/550e8400-e29b-41d4-a716-446655440000', {
  method: 'GET',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN'
  }
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`CampaignResponse`](#campaignresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Update Campaign

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#50E3C2", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ PATCH }}</span>
  <code>/api/campaigns/{campaign_id}</code>
</div>

Update campaign.

Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `campaign_id` | `string (uuid)` | ✅ |  |


#### Request Body (`application/json`)

See schema: [`CampaignUpdate`](#campaignupdate)

**Example:**

```json
{
  "name": "name",
  "status": "status"
}
```

#### Example Request

```bash
curl -X PATCH 'http://localhost:8000/api/campaigns/550e8400-e29b-41d4-a716-446655440000' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "name",
  "status": "status"
}'
```

```javascript
const response = await fetch('http://localhost:8000/api/campaigns/550e8400-e29b-41d4-a716-446655440000', {
  method: 'PATCH',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: "name",
    status: "status"
  })
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`CampaignResponse`](#campaignresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Delete Campaign

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#F93E3E", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ DELETE }}</span>
  <code>/api/campaigns/{campaign_id}</code>
</div>

Soft delete a campaign.

Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `campaign_id` | `string (uuid)` | ✅ |  |


#### Example Request

```bash
curl -X DELETE 'http://localhost:8000/api/campaigns/550e8400-e29b-41d4-a716-446655440000' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```javascript
const response = await fetch('http://localhost:8000/api/campaigns/550e8400-e29b-41d4-a716-446655440000', {
  method: 'DELETE',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN'
  }
});

const data = await response.json();
```

#### Responses

**204** - Successful Response



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Start Campaign

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#49CC90", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ POST }}</span>
  <code>/api/campaigns/{campaign_id}/start</code>
</div>

Start a campaign.

Changes status from DRAFT/SCHEDULED to SENDING.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `campaign_id` | `string (uuid)` | ✅ |  |


#### Example Request

```bash
curl -X POST 'http://localhost:8000/api/campaigns/550e8400-e29b-41d4-a716-446655440000/start' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```javascript
const response = await fetch('http://localhost:8000/api/campaigns/550e8400-e29b-41d4-a716-446655440000/start', {
  method: 'POST',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN'
  }
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`CampaignResponse`](#campaignresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Pause Campaign

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#49CC90", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ POST }}</span>
  <code>/api/campaigns/{campaign_id}/pause</code>
</div>

Pause a sending campaign.

Changes status from SENDING to SCHEDULED (paused state).
Note: In this system, SCHEDULED also represents a paused campaign.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `campaign_id` | `string (uuid)` | ✅ |  |


#### Example Request

```bash
curl -X POST 'http://localhost:8000/api/campaigns/550e8400-e29b-41d4-a716-446655440000/pause' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```javascript
const response = await fetch('http://localhost:8000/api/campaigns/550e8400-e29b-41d4-a716-446655440000/pause', {
  method: 'POST',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN'
  }
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`CampaignResponse`](#campaignresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


## Contacts

### Create Contact

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#49CC90", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ POST }}</span>
  <code>/api/contacts</code>
</div>

Create a new contact.

Phone number must be in E.164 format (e.g., +15551234567).
Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Request Body (`application/json`)

See schema: [`ContactCreate`](#contactcreate)

**Example:**

```json
{
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number": "phone_number",
  "name": "name",
  "tags": []
}
```

#### Example Request

```bash
curl -X POST 'http://localhost:8000/api/contacts' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number": "phone_number",
  "name": "name",
  "tags": []
}'
```

```javascript
const response = await fetch('http://localhost:8000/api/contacts', {
  method: 'POST',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    workspace_id: "550e8400-e29b-41d4-a716-446655440000",
    phone_number: "phone_number",
    name: "name",
    tags: []
  })
});

const data = await response.json();
```

#### Responses

**201** - Successful Response

Returns: [`ContactResponse`](#contactresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### List Contacts

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#61AFFE", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ GET }}</span>
  <code>/api/contacts</code>
</div>

List contacts for a workspace.

Supports filtering by tags, opt-in status, and search.
Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Query Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ | Workspace ID |
| `tags` | `any` | ❌ | Filter by tags (comma-separated) |
| `opted_in` | `any` | ❌ | Filter by opt-in status |
| `search` | `any` | ❌ | Search by name or phone |
| `limit` | `integer` | ❌ |  (default: `20`) |
| `offset` | `integer` | ❌ |  (default: `0`) |


#### Example Request

```bash
curl -X GET 'http://localhost:8000/api/contacts' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```javascript
const response = await fetch('http://localhost:8000/api/contacts?workspace_id=550e8400-e29b-41d4-a716-446655440000', {
  method: 'GET',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN'
  }
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`ContactListResponse`](#contactlistresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Get Contact

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#61AFFE", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ GET }}</span>
  <code>/api/contacts/{contact_id}</code>
</div>

Get contact details.

Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contact_id` | `string (uuid)` | ✅ |  |


#### Example Request

```bash
curl -X GET 'http://localhost:8000/api/contacts/550e8400-e29b-41d4-a716-446655440000' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```javascript
const response = await fetch('http://localhost:8000/api/contacts/550e8400-e29b-41d4-a716-446655440000', {
  method: 'GET',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN'
  }
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`ContactResponse`](#contactresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Update Contact

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#50E3C2", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ PATCH }}</span>
  <code>/api/contacts/{contact_id}</code>
</div>

Update a contact.

Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contact_id` | `string (uuid)` | ✅ |  |


#### Request Body (`application/json`)

See schema: [`ContactUpdate`](#contactupdate)

**Example:**

```json
{
  "name": "name",
  "tags": [],
  "opted_in": true
}
```

#### Example Request

```bash
curl -X PATCH 'http://localhost:8000/api/contacts/550e8400-e29b-41d4-a716-446655440000' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "name",
  "tags": [],
  "opted_in": true
}'
```

```javascript
const response = await fetch('http://localhost:8000/api/contacts/550e8400-e29b-41d4-a716-446655440000', {
  method: 'PATCH',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: "name",
    tags: [],
    opted_in: true
  })
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`ContactResponse`](#contactresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Delete Contact

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#F93E3E", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ DELETE }}</span>
  <code>/api/contacts/{contact_id}</code>
</div>

Soft delete a contact.

Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contact_id` | `string (uuid)` | ✅ |  |


#### Example Request

```bash
curl -X DELETE 'http://localhost:8000/api/contacts/550e8400-e29b-41d4-a716-446655440000' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```javascript
const response = await fetch('http://localhost:8000/api/contacts/550e8400-e29b-41d4-a716-446655440000', {
  method: 'DELETE',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN'
  }
});

const data = await response.json();
```

#### Responses

**204** - Successful Response



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Import Contacts

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#49CC90", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ POST }}</span>
  <code>/api/contacts/import</code>
</div>

Import contacts from CSV or Excel file.

Expected columns:
- phone (required): Phone number in E.164 format or common formats
- name (optional): Contact name
- labels/tags (optional): Comma or semicolon separated labels

Returns per-row import status.
Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Query Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ | Workspace ID |


#### Request Body (`multipart/form-data`)

See schema: [`Body_import_contacts_api_contacts_import_post`](#body_import_contacts_api_contacts_import_post)

**Example:**

```json
{
  "file": "file"
}
```

#### Example Request

```bash
curl -X POST 'http://localhost:8000/api/contacts/import' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json'
```

```javascript
const response = await fetch('http://localhost:8000/api/contacts/import?workspace_id=550e8400-e29b-41d4-a716-446655440000', {
  method: 'POST',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN',
    'Content-Type': 'application/json'
  }
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`ImportResponse`](#importresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


## Media

### Upload Media

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#49CC90", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ POST }}</span>
  <code>/api/media</code>
</div>

Upload a media file to Azure Blob Storage.

Accepts multipart/form-data with:
- workspace_id: UUID of the workspace
- file: The file to upload

File size limits:
- Images: 16 MB (JPEG, PNG, GIF, BMP)
- Videos: 100 MB (MP4, 3GPP, QuickTime)
- Audio: 16 MB (AAC, MP4, MPEG, AMR, OGG)
- Documents: 100 MB (PDF, Word, Excel, PowerPoint, Text)

Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Request Body (`multipart/form-data`)

See schema: [`Body_upload_media_api_media_post`](#body_upload_media_api_media_post)

**Example:**

```json
{
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "file": "file"
}
```

#### Example Request

```bash
curl -X POST 'http://localhost:8000/api/media' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json'
```

```javascript
const response = await fetch('http://localhost:8000/api/media', {
  method: 'POST',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN',
    'Content-Type': 'application/json'
  }
});

const data = await response.json();
```

#### Responses

**201** - Successful Response

Returns: [`MediaResponse`](#mediaresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### List Media

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#61AFFE", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ GET }}</span>
  <code>/api/media</code>
</div>

List media files for a workspace.

Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Query Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ | Workspace ID to filter by |
| `type` | `any` | ❌ | Filter by media type |
| `limit` | `integer` | ❌ |  (default: `20`) |
| `offset` | `integer` | ❌ |  (default: `0`) |


#### Example Request

```bash
curl -X GET 'http://localhost:8000/api/media' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```javascript
const response = await fetch('http://localhost:8000/api/media?workspace_id=550e8400-e29b-41d4-a716-446655440000', {
  method: 'GET',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN'
  }
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`MediaListResponse`](#medialistresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Get Media

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#61AFFE", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ GET }}</span>
  <code>/api/media/{media_id}</code>
</div>

Get media file details.

Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `media_id` | `string (uuid)` | ✅ |  |


#### Example Request

```bash
curl -X GET 'http://localhost:8000/api/media/550e8400-e29b-41d4-a716-446655440000' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```javascript
const response = await fetch('http://localhost:8000/api/media/550e8400-e29b-41d4-a716-446655440000', {
  method: 'GET',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN'
  }
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`MediaResponse`](#mediaresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Delete Media

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#F93E3E", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ DELETE }}</span>
  <code>/api/media/{media_id}</code>
</div>

Soft delete a media file.

Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `media_id` | `string (uuid)` | ✅ |  |


#### Example Request

```bash
curl -X DELETE 'http://localhost:8000/api/media/550e8400-e29b-41d4-a716-446655440000' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```javascript
const response = await fetch('http://localhost:8000/api/media/550e8400-e29b-41d4-a716-446655440000', {
  method: 'DELETE',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN'
  }
});

const data = await response.json();
```

#### Responses

**204** - Successful Response



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Download Media

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#61AFFE", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ GET }}</span>
  <code>/api/media/{media_id}/download</code>
</div>

Download a media file via redirect to SAS URL.

Returns a 307 redirect to a temporary Azure SAS URL (60 min expiry).
This approach avoids streaming file bytes through the API server.

Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `media_id` | `string (uuid)` | ✅ |  |


#### Example Request

```bash
curl -X GET 'http://localhost:8000/api/media/550e8400-e29b-41d4-a716-446655440000/download' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```javascript
const response = await fetch('http://localhost:8000/api/media/550e8400-e29b-41d4-a716-446655440000/download', {
  method: 'GET',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN'
  }
});

const data = await response.json();
```

#### Responses

**200** - Successful Response



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Get Media Url

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#61AFFE", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ GET }}</span>
  <code>/api/media/{media_id}/url</code>
</div>

Get a temporary signed URL for a media file.

Returns a JSON response with a temporary Azure SAS URL.
Configurable expiry from 5 to 1440 minutes (24 hours).

Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `media_id` | `string (uuid)` | ✅ |  |


**Query Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `expiry_minutes` | `integer` | ❌ | URL validity in minutes (default: `60`) |


#### Example Request

```bash
curl -X GET 'http://localhost:8000/api/media/550e8400-e29b-41d4-a716-446655440000/url' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```javascript
const response = await fetch('http://localhost:8000/api/media/550e8400-e29b-41d4-a716-446655440000/url', {
  method: 'GET',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN'
  }
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`MediaURLResponse`](#mediaurlresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


## Messages

### Send Text Message

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#49CC90", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ POST }}</span>
  <code>/api/messages/send/text</code>
</div>

Send a text message.

NOTE: This is a PLACEHOLDER endpoint for API scaffolding.
Actual implementation should:
1. Find or create contact and conversation
2. Create message record with conversation_id
3. Queue message to Redis for async sending via WhatsApp API
4. Return the queued message

Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Request Body (`application/json`)

See schema: [`SendTextMessageRequest`](#sendtextmessagerequest)

**Example:**

```json
{
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number_id": "550e8400-e29b-41d4-a716-446655440000",
  "to": "to",
  "text": "text"
}
```

#### Example Request

```bash
curl -X POST 'http://localhost:8000/api/messages/send/text' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number_id": "550e8400-e29b-41d4-a716-446655440000",
  "to": "to",
  "text": "text"
}'
```

```javascript
const response = await fetch('http://localhost:8000/api/messages/send/text', {
  method: 'POST',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    workspace_id: "550e8400-e29b-41d4-a716-446655440000",
    phone_number_id: "550e8400-e29b-41d4-a716-446655440000",
    to: "to",
    text: "text"
  })
});

const data = await response.json();
```

#### Responses

**201** - Successful Response

Returns: [`MessageResponse`](#messageresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Send Template Message

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#49CC90", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ POST }}</span>
  <code>/api/messages/send/template</code>
</div>

Send a template message.

NOTE: This is a PLACEHOLDER endpoint for API scaffolding.
Actual implementation should integrate with WhatsApp client,
create conversation, and queue the message.

Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Request Body (`application/json`)

See schema: [`SendTemplateMessageRequest`](#sendtemplatemessagerequest)

**Example:**

```json
{
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number_id": "550e8400-e29b-41d4-a716-446655440000",
  "to": "to",
  "template_name": "template_name",
  "template_language": "template_language",
  "components": {}
}
```

#### Example Request

```bash
curl -X POST 'http://localhost:8000/api/messages/send/template' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number_id": "550e8400-e29b-41d4-a716-446655440000",
  "to": "to",
  "template_name": "template_name",
  "template_language": "template_language",
  "components": {}
}'
```

```javascript
const response = await fetch('http://localhost:8000/api/messages/send/template', {
  method: 'POST',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    workspace_id: "550e8400-e29b-41d4-a716-446655440000",
    phone_number_id: "550e8400-e29b-41d4-a716-446655440000",
    to: "to",
    template_name: "template_name",
    template_language: "template_language",
    components: {}
  })
});

const data = await response.json();
```

#### Responses

**201** - Successful Response

Returns: [`MessageResponse`](#messageresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Send Media Message

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#49CC90", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ POST }}</span>
  <code>/api/messages/send/media</code>
</div>

Send a media message.

Validates the media file exists and has been uploaded,
then queues the message for async delivery.

Flow:
1. Validate workspace membership
2. Validate phone number
3. Validate media file exists and is ready
4. Generate SAS URL for media delivery
5. Queue message to outbound queue

Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Request Body (`application/json`)

See schema: [`SendMediaMessageRequest`](#sendmediamessagerequest)

**Example:**

```json
{
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number_id": "550e8400-e29b-41d4-a716-446655440000",
  "to": "to",
  "media_type": "media_type",
  "media_id": "550e8400-e29b-41d4-a716-446655440000",
  "caption": "caption"
}
```

#### Example Request

```bash
curl -X POST 'http://localhost:8000/api/messages/send/media' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number_id": "550e8400-e29b-41d4-a716-446655440000",
  "to": "to",
  "media_type": "media_type",
  "media_id": "550e8400-e29b-41d4-a716-446655440000",
  "caption": "caption"
}'
```

```javascript
const response = await fetch('http://localhost:8000/api/messages/send/media', {
  method: 'POST',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    workspace_id: "550e8400-e29b-41d4-a716-446655440000",
    phone_number_id: "550e8400-e29b-41d4-a716-446655440000",
    to: "to",
    media_type: "media_type",
    media_id: "550e8400-e29b-41d4-a716-446655440000",
    caption: "caption"
  })
});

const data = await response.json();
```

#### Responses

**201** - Successful Response

Returns: [`MessageQueuedResponse`](#messagequeuedresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Get Message Status

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#61AFFE", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ GET }}</span>
  <code>/api/messages/{message_id}/status</code>
</div>

Get message delivery status.

Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `message_id` | `string (uuid)` | ✅ |  |


#### Example Request

```bash
curl -X GET 'http://localhost:8000/api/messages/550e8400-e29b-41d4-a716-446655440000/status' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```javascript
const response = await fetch('http://localhost:8000/api/messages/550e8400-e29b-41d4-a716-446655440000/status', {
  method: 'GET',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN'
  }
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`MessageStatusResponse`](#messagestatusresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


## Phone Numbers

### Create Phone Number

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#49CC90", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ POST }}</span>
  <code>/api/workspaces/{workspace_id}/phone-numbers</code>
</div>

Register a new WhatsApp Business phone number.

Flow:
1. Verify workspace membership (OWNER or ADMIN)
2. Validate access_token with Meta API
3. Fetch phone number details from Meta
4. Check if phone_number_id already exists
5. Create PhoneNumber record
6. Return PhoneNumberResponse

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ |  |


#### Request Body (`application/json`)

See schema: [`PhoneNumberCreate`](#phonenumbercreate)

**Example:**

```json
{
  "phone_number_id": "phone_number_id",
  "access_token": "access_token",
  "display_name": "display_name",
  "business_id": "business_id"
}
```

#### Example Request

```bash
curl -X POST 'http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/phone-numbers' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "phone_number_id": "phone_number_id",
  "access_token": "access_token",
  "display_name": "display_name",
  "business_id": "business_id"
}'
```

```javascript
const response = await fetch('http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/phone-numbers', {
  method: 'POST',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    phone_number_id: "phone_number_id",
    access_token: "access_token",
    display_name: "display_name",
    business_id: "business_id"
  })
});

const data = await response.json();
```

#### Responses

**201** - Successful Response

Returns: [`PhoneNumberResponse`](#phonenumberresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### List Phone Numbers

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#61AFFE", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ GET }}</span>
  <code>/api/phone-numbers</code>
</div>

List phone numbers for a workspace.

Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Query Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `status` | `any` | ❌ | Filter by status (pending, active, disabled) |
| `limit` | `integer` | ❌ | Results per page (default: `20`) |
| `offset` | `integer` | ❌ | Offset for pagination (default: `0`) |


#### Example Request

```bash
curl -X GET 'http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/phone-numbers' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```javascript
const response = await fetch('http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/phone-numbers', {
  method: 'GET',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN'
  }
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`PhoneNumberListResponse`](#phonenumberlistresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Get Phone Number

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#61AFFE", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ GET }}</span>
  <code>/api/phone-numbers/{phone_number_id}</code>
</div>

Get details of a specific phone number.

Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ |  |
| `phone_number_id` | `string (uuid)` | ✅ |  |


#### Example Request

```bash
curl -X GET 'http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/phone-numbers/550e8400-e29b-41d4-a716-446655440000' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```javascript
const response = await fetch('http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/phone-numbers/550e8400-e29b-41d4-a716-446655440000', {
  method: 'GET',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN'
  }
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`PhoneNumberResponse`](#phonenumberresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Update Phone Number

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#50E3C2", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ PATCH }}</span>
  <code>/api/phone-numbers/{phone_number_id}</code>
</div>

Update phone number settings.

Requires OWNER or ADMIN role.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ |  |
| `phone_number_id` | `string (uuid)` | ✅ |  |


#### Request Body (`application/json`)

See schema: [`PhoneNumberUpdate`](#phonenumberupdate)

**Example:**

```json
{
  "display_name": "display_name",
  "access_token": "access_token",
  "status": "status"
}
```

#### Example Request

```bash
curl -X PATCH 'http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/phone-numbers/550e8400-e29b-41d4-a716-446655440000' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "display_name": "display_name",
  "access_token": "access_token",
  "status": "status"
}'
```

```javascript
const response = await fetch('http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/phone-numbers/550e8400-e29b-41d4-a716-446655440000', {
  method: 'PATCH',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    display_name: "display_name",
    access_token: "access_token",
    status: "status"
  })
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`PhoneNumberResponse`](#phonenumberresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Delete Phone Number

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#F93E3E", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ DELETE }}</span>
  <code>/api/phone-numbers/{phone_number_id}</code>
</div>

Soft delete a phone number.

Requires OWNER or ADMIN role.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ |  |
| `phone_number_id` | `string (uuid)` | ✅ |  |


#### Example Request

```bash
curl -X DELETE 'http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/phone-numbers/550e8400-e29b-41d4-a716-446655440000' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```javascript
const response = await fetch('http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/phone-numbers/550e8400-e29b-41d4-a716-446655440000', {
  method: 'DELETE',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN'
  }
});

const data = await response.json();
```

#### Responses

**204** - Successful Response



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Sync Phone Number

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#49CC90", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ POST }}</span>
  <code>/api/workspaces/{workspace_id}/phone-numbers/{phone_number_id}/sync</code>
</div>

Sync phone number data from Meta API.

Fetches the latest quality rating, message limit, and tier from Meta.
Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ |  |
| `phone_number_id` | `string (uuid)` | ✅ |  |


#### Example Request

```bash
curl -X POST 'http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/phone-numbers/550e8400-e29b-41d4-a716-446655440000/sync' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```javascript
const response = await fetch('http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/phone-numbers/550e8400-e29b-41d4-a716-446655440000/sync', {
  method: 'POST',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN'
  }
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`PhoneNumberSyncResponse`](#phonenumbersyncresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Exchange Token For Long Term

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#49CC90", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ POST }}</span>
  <code>/api/workspaces/{workspace_id}/phone-numbers/{phone_number_id}/exchange-token</code>
</div>

Exchange short-lived access token for long-lived token.

This endpoint attempts to exchange the current access token for a long-lived
token (typically 60 days vs 1 hour). This is useful when you have a short-lived
user access token and want to convert it to a long-lived one.

Note: System user tokens are already long-lived and don't need exchange.

Requires workspace admin access.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ |  |
| `phone_number_id` | `string (uuid)` | ✅ |  |


#### Example Request

```bash
curl -X POST 'http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/phone-numbers/550e8400-e29b-41d4-a716-446655440000/exchange-token' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```javascript
const response = await fetch('http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/phone-numbers/550e8400-e29b-41d4-a716-446655440000/exchange-token', {
  method: 'POST',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN'
  }
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`PhoneNumberResponse`](#phonenumberresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


## Templates

### Create Template

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#49CC90", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ POST }}</span>
  <code>/api/templates</code>
</div>

Create a new WhatsApp message template.

Templates must be approved by Meta before they can be used.
The template will be created with PENDING status.

Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Request Body (`application/json`)

See schema: [`TemplateCreate`](#templatecreate)

**Example:**

```json
{
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "name",
  "category": "category",
  "language": "language",
  "components": {}
}
```

#### Example Request

```bash
curl -X POST 'http://localhost:8000/api/templates' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "name",
  "category": "category",
  "language": "language",
  "components": {}
}'
```

```javascript
const response = await fetch('http://localhost:8000/api/templates', {
  method: 'POST',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    workspace_id: "550e8400-e29b-41d4-a716-446655440000",
    phone_number_id: "550e8400-e29b-41d4-a716-446655440000",
    name: "name",
    category: "category",
    language: "language",
    components: {}
  })
});

const data = await response.json();
```

#### Responses

**201** - Successful Response

Returns: [`TemplateResponse`](#templateresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### List Templates

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#61AFFE", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ GET }}</span>
  <code>/api/templates</code>
</div>

List templates for a workspace.

Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Query Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ | Workspace ID to filter by |
| `phone_number_id` | `any` | ❌ | Filter by phone number |
| `status` | `any` | ❌ | Filter by status |
| `category` | `any` | ❌ | Filter by category |
| `limit` | `integer` | ❌ |  (default: `20`) |
| `offset` | `integer` | ❌ |  (default: `0`) |


#### Example Request

```bash
curl -X GET 'http://localhost:8000/api/templates' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```javascript
const response = await fetch('http://localhost:8000/api/templates?workspace_id=550e8400-e29b-41d4-a716-446655440000', {
  method: 'GET',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN'
  }
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`TemplateListResponse`](#templatelistresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Get Template

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#61AFFE", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ GET }}</span>
  <code>/api/templates/{template_id}</code>
</div>

Get template details.

Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `template_id` | `string (uuid)` | ✅ |  |


#### Example Request

```bash
curl -X GET 'http://localhost:8000/api/templates/550e8400-e29b-41d4-a716-446655440000' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```javascript
const response = await fetch('http://localhost:8000/api/templates/550e8400-e29b-41d4-a716-446655440000', {
  method: 'GET',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN'
  }
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`TemplateResponse`](#templateresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Update Template

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#50E3C2", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ PATCH }}</span>
  <code>/api/templates/{template_id}</code>
</div>

Update template.

Only components and status can be updated.
Status changes are typically managed by Meta webhook updates.

Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `template_id` | `string (uuid)` | ✅ |  |


#### Request Body (`application/json`)

See schema: [`TemplateUpdate`](#templateupdate)

**Example:**

```json
{
  "components": {},
  "status": "status"
}
```

#### Example Request

```bash
curl -X PATCH 'http://localhost:8000/api/templates/550e8400-e29b-41d4-a716-446655440000' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "components": {},
  "status": "status"
}'
```

```javascript
const response = await fetch('http://localhost:8000/api/templates/550e8400-e29b-41d4-a716-446655440000', {
  method: 'PATCH',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    components: {},
    status: "status"
  })
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`TemplateResponse`](#templateresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Delete Template

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#F93E3E", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ DELETE }}</span>
  <code>/api/templates/{template_id}</code>
</div>

Soft delete a template.

Requires workspace membership.

:::info Authentication Required

This endpoint requires authentication.

:::

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `template_id` | `string (uuid)` | ✅ |  |


#### Example Request

```bash
curl -X DELETE 'http://localhost:8000/api/templates/550e8400-e29b-41d4-a716-446655440000' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```javascript
const response = await fetch('http://localhost:8000/api/templates/550e8400-e29b-41d4-a716-446655440000', {
  method: 'DELETE',
  headers: {
    Authorization: 'Bearer YOUR_ACCESS_TOKEN'
  }
});

const data = await response.json();
```

#### Responses

**204** - Successful Response



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


## Campaigns

### Create Campaign

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#49CC90", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ POST }}</span>
  <code>/api/workspaces/{workspace_id}/campaigns</code>
</div>

Create a new campaign.

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ |  |

#### Request Body (`application/json`)

See schema: [`CampaignCreate`](#campaigncreate)

**Example:**

```json
{
  "phone_number_id": "phone_number_id",
  "template_id": "template_id",
  "name": "name"
}
```

#### Example Request

```bash
curl -X POST 'http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/campaigns' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "phone_number_id": "phone_number_id",
  "template_id": "template_id",
  "name": "name"
}'
```

#### Responses

**201** - Successful Response

Returns: [`CampaignResponse`](#campaignresponse)

---

### List Campaigns

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#61AFFE", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ GET }}</span>
  <code>/api/workspaces/{workspace_id}/campaigns</code>
</div>

List campaigns for a workspace.

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ |  |

**Query Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `status` | `any` | ❌ | Filter by status |
| `phone_number_id` | `string (uuid)` | ❌ | Filter by phone number |
| `limit` | `integer` | ❌ | Results per page (default: `20`) |
| `offset` | `integer` | ❌ | Offset for pagination (default: `0`) |

#### Example Request

```bash
curl -X GET 'http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/campaigns' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

#### Responses

**200** - Successful Response

Returns: [`CampaignListResponse`](#campaignlistresponse)

---

### Get Campaign

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#61AFFE", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ GET }}</span>
  <code>/api/workspaces/{workspace_id}/campaigns/{campaign_id}</code>
</div>

Get campaign details.

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ |  |
| `campaign_id` | `string (uuid)` | ✅ |  |

#### Responses

**200** - Successful Response

Returns: [`CampaignResponse`](#campaignresponse)

---

### Update Campaign

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#50E3C2", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ PATCH }}</span>
  <code>/api/workspaces/{workspace_id}/campaigns/{campaign_id}</code>
</div>

Update campaign.

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ |  |
| `campaign_id` | `string (uuid)` | ✅ |  |

#### Request Body (`application/json`)

See schema: [`CampaignUpdate`](#campaignupdate)

#### Responses

**200** - Successful Response

Returns: [`CampaignResponse`](#campaignresponse)

---

### Delete Campaign

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#F93E3E", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ DELETE }}</span>
  <code>/api/workspaces/{workspace_id}/campaigns/{campaign_id}</code>
</div>

Soft delete a campaign.

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ |  |
| `campaign_id` | `string (uuid)` | ✅ |  |

#### Responses

**204** - Successful Response

---

### Execute Campaign

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#49CC90", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ POST }}</span>
  <code>/api/workspaces/{workspace_id}/campaigns/{campaign_id}/execute</code>
</div>

Start campaign execution. Queues the campaign for processing.

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ |  |
| `campaign_id` | `string (uuid)` | ✅ |  |

#### Responses

**200** - Successful Response

Returns: [`CampaignResponse`](#campaignresponse)

---

### Pause Campaign

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#49CC90", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ POST }}</span>
  <code>/api/workspaces/{workspace_id}/campaigns/{campaign_id}/pause</code>
</div>

Pause a running campaign.

#### Responses

**200** - Successful Response

Returns: [`CampaignResponse`](#campaignresponse)

---

### Cancel Campaign

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#49CC90", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ POST }}</span>
  <code>/api/workspaces/{workspace_id}/campaigns/{campaign_id}/cancel</code>
</div>

Cancel a running or scheduled campaign.

#### Responses

**200** - Successful Response

Returns: [`CampaignResponse`](#campaignresponse)

---


## Webhooks

### Verify Webhook

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#61AFFE", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ GET }}</span>
  <code>/webhook</code>
</div>

Webhook Verification (Setup Only)

Meta calls this ONCE when you first configure the webhook.
Must return the challenge value to verify ownership.

#### Example Request

```bash
curl -X GET 'http://localhost:8000/webhook'
```

```javascript
const response = await fetch('http://localhost:8000/webhook', {
  method: 'GET',
});

const data = await response.json();
```

#### Responses

**200** - Successful Response



---


### Receive Webhook

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#49CC90", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ POST }}</span>
  <code>/webhook</code>
</div>

Main Webhook Endpoint - Receives ALL events from Meta

Flow:
  1. Read raw body
  2. Verify HMAC signature
  3. Parse JSON
  4.  Check idempotency (skip duplicates)
  5. Route to Redis queue by event type
  6. Return 200 OK immediately

#### Parameters

**Headers**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `X-Hub-Signature-256` | `any` | ❌ |  |


#### Example Request

```bash
curl -X POST 'http://localhost:8000/webhook'
```

```javascript
const response = await fetch('http://localhost:8000/webhook', {
  method: 'POST',
});

const data = await response.json();
```

#### Responses

**200** - Successful Response



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


## Workspaces

### List Workspaces

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#61AFFE", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ GET }}</span>
  <code>/api/workspaces</code>
</div>

List all workspaces user is a member of.

#### Example Request

```bash
curl -X GET 'http://localhost:8000/api/workspaces'
```

```javascript
const response = await fetch('http://localhost:8000/api/workspaces', {
  method: 'GET',
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: Array of [`WorkspaceListResponse`](#workspacelistresponse)



---


### Create Workspace

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#49CC90", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ POST }}</span>
  <code>/api/workspaces</code>
</div>

Create a new workspace.

#### Request Body (`application/json`)

See schema: [`WorkspaceCreate`](#workspacecreate)

**Example:**

```json
{
  "name": "name",
  "plan": "free"
}
```

#### Example Request

```bash
curl -X POST 'http://localhost:8000/api/workspaces' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "name",
  "plan": "free"
}'
```

```javascript
const response = await fetch('http://localhost:8000/api/workspaces', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: "name",
    plan: "free"
  })
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`WorkspaceResponse`](#workspaceresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Get Workspace

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#61AFFE", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ GET }}</span>
  <code>/api/workspaces/{workspace_id}</code>
</div>

Get specific workspace. Requires membership.

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ |  |


#### Example Request

```bash
curl -X GET 'http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000'
```

```javascript
const response = await fetch('http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000', {
  method: 'GET',
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`WorkspaceResponse`](#workspaceresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Update Workspace

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#50E3C2", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ PATCH }}</span>
  <code>/api/workspaces/{workspace_id}</code>
</div>

Update workspace. Requires OWNER or ADMIN role.

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ |  |


#### Request Body (`application/json`)

See schema: [`WorkspaceUpdate`](#workspaceupdate)

**Example:**

```json
{
  "name": "name",
  "plan": "{...}",
  "status": "{...}",
  "settings": {}
}
```

#### Example Request

```bash
curl -X PATCH 'http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "name",
  "plan": "{...}",
  "status": "{...}",
  "settings": {}
}'
```

```javascript
const response = await fetch('http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000', {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: "name",
    plan: "{...}",
    status: "{...}",
    settings: {}
  })
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`WorkspaceResponse`](#workspaceresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Delete Workspace

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#F93E3E", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ DELETE }}</span>
  <code>/api/workspaces/{workspace_id}</code>
</div>

Soft delete workspace. Requires OWNER role only.

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ |  |


#### Example Request

```bash
curl -X DELETE 'http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000'
```

```javascript
const response = await fetch('http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000', {
  method: 'DELETE',
});

const data = await response.json();
```

#### Responses

**204** - Successful Response



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### List Workspace Members

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#61AFFE", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ GET }}</span>
  <code>/api/workspaces/{workspace_id}/members</code>
</div>

List workspace members. Requires membership.

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ |  |


#### Example Request

```bash
curl -X GET 'http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/members'
```

```javascript
const response = await fetch('http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/members', {
  method: 'GET',
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: Array of [`WorkspaceMemberResponse`](#workspacememberresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


### Add Workspace Member

<div style={{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}>
  <span style={{backgroundColor: "#49CC90", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}>{{ POST }}</span>
  <code>/api/workspaces/{workspace_id}/members</code>
</div>

Add member to workspace. Requires OWNER or ADMIN role.

#### Parameters

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ |  |


#### Request Body (`application/json`)

See schema: [`AddMemberRequest`](#addmemberrequest)

**Example:**

```json
{
  "user_email": "user@example.com",
  "role": "OWNER"
}
```

#### Example Request

```bash
curl -X POST 'http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/members' \
  -H 'Content-Type: application/json' \
  -d '{
  "user_email": "user@example.com",
  "role": "OWNER"
}'
```

```javascript
const response = await fetch('http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/members', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    user_email: "user@example.com",
    role: "OWNER"
  })
});

const data = await response.json();
```

#### Responses

**200** - Successful Response

Returns: [`WorkspaceMemberResponse`](#workspacememberresponse)



**422** - Validation Error

Returns: [`HTTPValidationError`](#httpvalidationerror)



---


## Data Schemas

Complete reference for all data models used in the API.


### AddMemberRequest

<a id="addmemberrequest"></a>

Request model for adding a member to a workspace

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `user_email` | `string (email)` | ✅ |  |
| `role` | `MemberRole` | ❌ |  Default: `MEMBER` |


**Example:**

```json
{
  "user_email": "user@example.com",
  "role": "OWNER"
}
```



### Body_import_contacts_api_contacts_import_post

<a id="body_import_contacts_api_contacts_import_post"></a>

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `file` | `string (binary)` | ✅ | CSV or Excel file |


**Example:**

```json
{
  "file": "file"
}
```



### Body_upload_media_api_media_post

<a id="body_upload_media_api_media_post"></a>

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ | Workspace ID |
| `file` | `string (binary)` | ✅ | File to upload |


**Example:**

```json
{
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "file": "file"
}
```



### CampaignCreate

<a id="campaigncreate"></a>

Schema for creating a new campaign

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ |  |
| `phone_number_id` | `string (uuid)` | ✅ |  |
| `template_id` | `string (uuid) (nullable)` | ❌ |  |
| `name` | `string` | ✅ |  (minLength: 1, maxLength: 255) |


**Example:**

```json
{
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number_id": "550e8400-e29b-41d4-a716-446655440000",
  "template_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "name"
}
```



### CampaignListResponse

<a id="campaignlistresponse"></a>

Schema for paginated campaign list

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `data` | `CampaignResponse[]` | ✅ |  |
| `total` | `integer` | ✅ |  |
| `limit` | `integer` | ✅ |  |
| `offset` | `integer` | ✅ |  |


**Example:**

```json
{
  "data": [],
  "total": 0,
  "limit": 0,
  "offset": 0
}
```



### CampaignResponse

<a id="campaignresponse"></a>

Schema for campaign response

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | `string (uuid)` | ✅ |  |
| `workspace_id` | `string (uuid)` | ✅ |  |
| `phone_number_id` | `string (uuid)` | ✅ |  |
| `template_id` | `string (uuid) (nullable)` | ✅ |  |
| `name` | `string` | ✅ |  |
| `total_contacts` | `integer` | ✅ |  |
| `sent_count` | `integer` | ✅ |  |
| `delivered_count` | `integer` | ✅ |  |
| `read_count` | `integer` | ✅ |  |
| `failed_count` | `integer` | ✅ |  |
| `status` | `string` | ✅ |  |


**Example:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number_id": "550e8400-e29b-41d4-a716-446655440000",
  "template_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "name",
  "total_contacts": 0,
  "sent_count": 0,
  "delivered_count": 0,
  "read_count": 0,
  "failed_count": 0,
  "status": "status"
}
```



### CampaignUpdate

<a id="campaignupdate"></a>

Schema for updating campaign

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | `string (nullable)` | ❌ |  |
| `status` | `string (nullable)` | ❌ |  |


**Example:**

```json
{
  "name": "name",
  "status": "status"
}
```



### ContactCreate

<a id="contactcreate"></a>

Schema for creating a new contact

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ |  |
| `phone_number` | `string` | ✅ | Phone number in E.164 format (e.g., +15551234567) |
| `name` | `string (nullable)` | ❌ |  |
| `tags` | `string[] (nullable)` | ❌ | Labels/tags for the contact |


**Example:**

```json
{
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number": "phone_number",
  "name": "name",
  "tags": []
}
```



### ContactListResponse

<a id="contactlistresponse"></a>

Schema for paginated contact list

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `data` | `ContactResponse[]` | ✅ |  |
| `total` | `integer` | ✅ |  |
| `limit` | `integer` | ✅ |  |
| `offset` | `integer` | ✅ |  |


**Example:**

```json
{
  "data": [],
  "total": 0,
  "limit": 0,
  "offset": 0
}
```



### ContactResponse

<a id="contactresponse"></a>

Schema for contact response

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | `string (uuid)` | ✅ |  |
| `workspace_id` | `string (uuid)` | ✅ |  |
| `wa_id` | `string` | ✅ |  |
| `phone_number` | `string` | ✅ |  |
| `name` | `string (nullable)` | ✅ |  |
| `opted_in` | `boolean` | ✅ |  |
| `tags` | `string[] (nullable)` | ✅ |  |
| `created_at` | `string (date-time)` | ✅ |  |
| `updated_at` | `string (date-time)` | ✅ |  |


**Example:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "wa_id": "wa_id",
  "phone_number": "phone_number",
  "name": "name",
  "opted_in": true,
  "tags": [],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```



### ContactUpdate

<a id="contactupdate"></a>

Schema for updating a contact

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | `string (nullable)` | ❌ |  |
| `tags` | `string[] (nullable)` | ❌ |  |
| `opted_in` | `boolean (nullable)` | ❌ |  |


**Example:**

```json
{
  "name": "name",
  "tags": [],
  "opted_in": true
}
```



### HTTPValidationError

<a id="httpvalidationerror"></a>

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `detail` | `ValidationError[]` | ❌ |  |


**Example:**

```json
{
  "detail": []
}
```



### ImportResponse

<a id="importresponse"></a>

Schema for import response

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `total_rows` | `integer` | ✅ |  |
| `imported` | `integer` | ✅ |  |
| `updated` | `integer` | ✅ |  |
| `failed` | `integer` | ✅ |  |
| `results` | `ImportRowResult[]` | ✅ |  |


**Example:**

```json
{
  "total_rows": 0,
  "imported": 0,
  "updated": 0,
  "failed": 0,
  "results": []
}
```



### ImportRowResult

<a id="importrowresult"></a>

Result for a single import row

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `row_number` | `integer` | ✅ |  |
| `phone_number` | `string (nullable)` | ✅ |  |
| `status` | `string` | ✅ |  |
| `reason` | `string (nullable)` | ❌ |  |


**Example:**

```json
{
  "row_number": 0,
  "phone_number": "phone_number",
  "status": "status",
  "reason": "reason"
}
```



### MediaListResponse

<a id="medialistresponse"></a>

Schema for paginated media list

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `data` | `MediaResponse[]` | ✅ |  |
| `total` | `integer` | ✅ |  |
| `limit` | `integer` | ✅ |  |
| `offset` | `integer` | ✅ |  |


**Example:**

```json
{
  "data": [],
  "total": 0,
  "limit": 0,
  "offset": 0
}
```



### MediaResponse

<a id="mediaresponse"></a>

Schema for media file response

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | `string (uuid)` | ✅ |  |
| `workspace_id` | `string (uuid)` | ✅ |  |
| `type` | `string` | ✅ |  |
| `original_url` | `string (nullable)` | ❌ |  |
| `storage_url` | `string (nullable)` | ❌ |  |
| `file_name` | `string (nullable)` | ❌ |  |
| `file_size` | `integer (nullable)` | ❌ |  |
| `mime_type` | `string (nullable)` | ❌ |  |
| `uploaded_by` | `string (uuid) (nullable)` | ❌ |  |
| `created_at` | `string (date-time)` | ✅ |  |
| `updated_at` | `string (date-time)` | ✅ |  |


**Example:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "type",
  "original_url": "original_url",
  "storage_url": "storage_url",
  "file_name": "file_name",
  "file_size": 0,
  "mime_type": "mime_type",
  "uploaded_by": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```



### MediaURLResponse

<a id="mediaurlresponse"></a>

Schema for temporary URL response

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `url` | `string` | ✅ |  |
| `expires_in_minutes` | `integer` | ✅ | URL validity in minutes |
| `expires_at` | `string (date-time)` | ✅ | Expiration timestamp |


**Example:**

```json
{
  "url": "url",
  "expires_in_minutes": 0,
  "expires_at": "2024-01-01T00:00:00Z"
}
```



### MemberRole

<a id="memberrole"></a>

**Enum Values:** `OWNER | ADMIN | MEMBER | AGENT`


### MemberStatus

<a id="memberstatus"></a>

**Enum Values:** `pending | active | suspended`


### MessageQueuedResponse

<a id="messagequeuedresponse"></a>

Response for queued message

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | `string (uuid)` | ✅ |  |
| `workspace_id` | `string (uuid)` | ✅ |  |
| `phone_number_id` | `string (uuid)` | ✅ |  |
| `to_number` | `string` | ✅ |  |
| `type` | `string` | ✅ |  |
| `status` | `string` | ✅ |  |
| `media_id` | `string (uuid) (nullable)` | ❌ |  |
| `queued` | `boolean` | ❌ |  Default: `True` |


**Example:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number_id": "550e8400-e29b-41d4-a716-446655440000",
  "to_number": "to_number",
  "type": "type",
  "status": "status",
  "media_id": "550e8400-e29b-41d4-a716-446655440000",
  "queued": true
}
```



### MessageResponse

<a id="messageresponse"></a>

Schema for message response

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | `string (uuid)` | ✅ |  |
| `workspace_id` | `string (uuid)` | ✅ |  |
| `phone_number_id` | `string (uuid)` | ✅ |  |
| `wa_message_id` | `string (nullable)` | ✅ |  |
| `direction` | `string` | ✅ |  |
| `from_number` | `string` | ✅ |  |
| `to_number` | `string` | ✅ |  |
| `type` | `string` | ✅ |  |
| `status` | `string` | ✅ |  |


**Example:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number_id": "550e8400-e29b-41d4-a716-446655440000",
  "wa_message_id": "wa_message_id",
  "direction": "direction",
  "from_number": "from_number",
  "to_number": "to_number",
  "type": "type",
  "status": "status"
}
```



### MessageStatusResponse

<a id="messagestatusresponse"></a>

Schema for message status response

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | `string (uuid)` | ✅ |  |
| `wa_message_id` | `string (nullable)` | ✅ |  |
| `status` | `string` | ✅ |  |
| `delivered_at` | `string (nullable)` | ✅ |  |
| `read_at` | `string (nullable)` | ✅ |  |


**Example:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "wa_message_id": "wa_message_id",
  "status": "status",
  "delivered_at": "delivered_at",
  "read_at": "read_at"
}
```



### PhoneNumberCreate

<a id="phonenumbercreate"></a>

Request schema for registering a new phone number.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ | Workspace UUID |
| `phone_number_id` | `string` | ✅ | Meta's Phone Number ID from Business Suite |
| `access_token` | `string` | ✅ | System User Access Token with whatsapp_business_messaging permission |
| `display_name` | `string (nullable)` | ❌ | Friendly name |
| `business_id` | `string (nullable)` | ❌ | WhatsApp Business Account ID (WABA ID) |


**Example:**

```json
{
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number_id": "phone_number_id",
  "access_token": "access_token",
  "display_name": "display_name",
  "business_id": "business_id"
}
```



### PhoneNumberListResponse

<a id="phonenumberlistresponse"></a>

Paginated list of phone numbers.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `data` | `PhoneNumberResponse[]` | ✅ |  |
| `total` | `integer` | ✅ |  |
| `limit` | `integer` | ✅ |  |
| `offset` | `integer` | ✅ |  |


**Example:**

```json
{
  "data": [],
  "total": 0,
  "limit": 0,
  "offset": 0
}
```



### PhoneNumberResponse

<a id="phonenumberresponse"></a>

Response schema for full phone number details.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | `string (uuid)` | ✅ |  |
| `workspace_id` | `string (uuid)` | ✅ |  |
| `phone_number` | `string` | ✅ |  |
| `phone_number_id` | `string` | ✅ |  |
| `display_name` | `string (nullable)` | ❌ |  |
| `business_id` | `string (nullable)` | ❌ |  |
| `quality_rating` | `string` | ❌ | GREEN/YELLOW/RED/UNKNOWN Default: `UNKNOWN` |
| `message_limit` | `integer` | ❌ |  Default: `1000` |
| `tier` | `string (nullable)` | ❌ |  |
| `status` | `string` | ❌ |  Default: `pending` |
| `verified_at` | `string (date-time) (nullable)` | ❌ |  |
| `created_at` | `string (date-time)` | ✅ |  |
| `updated_at` | `string (date-time)` | ✅ |  |


**Example:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number": "phone_number",
  "phone_number_id": "phone_number_id",
  "display_name": "display_name",
  "business_id": "business_id",
  "quality_rating": "quality_rating",
  "message_limit": 0,
  "tier": "tier",
  "status": "status",
  "verified_at": "2024-01-01T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```



### PhoneNumberSyncResponse

<a id="phonenumbersyncresponse"></a>

Response for sync operation.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | `string (uuid)` | ✅ |  |
| `synced_at` | `string (date-time)` | ✅ |  |
| `phone_number` | `string` | ✅ |  |
| `quality_rating` | `string` | ✅ |  |
| `message_limit` | `integer` | ✅ |  |
| `tier` | `string (nullable)` | ❌ |  |
| `status` | `string` | ✅ |  |


**Example:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "synced_at": "2024-01-01T00:00:00Z",
  "phone_number": "phone_number",
  "quality_rating": "quality_rating",
  "message_limit": 0,
  "tier": "tier",
  "status": "status"
}
```



### PhoneNumberUpdate

<a id="phonenumberupdate"></a>

Request schema for updating phone number settings.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `display_name` | `string (nullable)` | ❌ | Friendly name |
| `access_token` | `string (nullable)` | ❌ | Will be validated if provided |
| `status` | `string (nullable)` | ❌ | Status: pending, active, or disabled |


**Example:**

```json
{
  "display_name": "display_name",
  "access_token": "access_token",
  "status": "status"
}
```



### Provider

<a id="provider"></a>

Login providers

**Enum Values:** `Email | Google | GitHub`


### SendMediaMessageRequest

<a id="sendmediamessagerequest"></a>

Schema for sending a media message

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ |  |
| `phone_number_id` | `string (uuid)` | ✅ |  |
| `to` | `string` | ✅ | Recipient phone number |
| `media_type` | `string` | ✅ | Type: image, video, audio, document |
| `media_id` | `string (uuid)` | ✅ | Media file ID from /api/media |
| `caption` | `string (nullable)` | ❌ | Optional caption |


**Example:**

```json
{
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number_id": "550e8400-e29b-41d4-a716-446655440000",
  "to": "to",
  "media_type": "media_type",
  "media_id": "550e8400-e29b-41d4-a716-446655440000",
  "caption": "caption"
}
```



### SendTemplateMessageRequest

<a id="sendtemplatemessagerequest"></a>

Schema for sending a template message

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ |  |
| `phone_number_id` | `string (uuid)` | ✅ |  |
| `to` | `string` | ✅ | Recipient phone number |
| `template_name` | `string` | ✅ |  |
| `template_language` | `string` | ❌ |  Default: `en` |
| `components` | `object (nullable)` | ❌ |  |


**Example:**

```json
{
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number_id": "550e8400-e29b-41d4-a716-446655440000",
  "to": "to",
  "template_name": "template_name",
  "template_language": "template_language",
  "components": {}
}
```



### SendTextMessageRequest

<a id="sendtextmessagerequest"></a>

Schema for sending a text message

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ |  |
| `phone_number_id` | `string (uuid)` | ✅ |  |
| `to` | `string` | ✅ | Recipient phone number |
| `text` | `string` | ✅ | Message text (minLength: 1) |


**Example:**

```json
{
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number_id": "550e8400-e29b-41d4-a716-446655440000",
  "to": "to",
  "text": "text"
}
```



### SigninResponse

<a id="signinresponse"></a>

Response model for successful login

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `user_id` | `string (uuid)` | ✅ |  |
| `access_token` | `string` | ✅ |  |
| `token_type` | `string` | ❌ |  Default: `bearer` |


**Example:**

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "access_token": "access_token",
  "token_type": "token_type"
}
```



### Signup

<a id="signup"></a>

Request model for Signup

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `email` | `string (email)` | ✅ |  |
| `password` | `string` | ✅ |  |
| `name` | `string (nullable)` | ❌ |  |


**Example:**

```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "name": "name"
}
```



### SignupResponse

<a id="signupresponse"></a>

Response model for successful signup

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `user_id` | `string (uuid)` | ✅ |  |
| `name` | `string` | ✅ |  |
| `email` | `string (email)` | ✅ |  |


**Example:**

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "name",
  "email": "user@example.com"
}
```



### TemplateCreate

<a id="templatecreate"></a>

Schema for creating a new template

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `workspace_id` | `string (uuid)` | ✅ |  |
| `phone_number_id` | `string (uuid)` | ✅ |  |
| `name` | `string` | ✅ | Template name (lowercase, no spaces) (minLength: 1, maxLength: 255) |
| `category` | `string` | ✅ | Template category: MARKETING, UTILITY, or AUTHENTICATION |
| `language` | `string` | ❌ | Language code (e.g., 'en', 'es', 'fr') Default: `en` |
| `components` | `object` | ✅ | Template components (header, body, footer, buttons) |


**Example:**

```json
{
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "name",
  "category": "category",
  "language": "language",
  "components": {}
}
```



### TemplateListResponse

<a id="templatelistresponse"></a>

Schema for paginated template list

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `data` | `TemplateResponse[]` | ✅ |  |
| `total` | `integer` | ✅ |  |
| `limit` | `integer` | ✅ |  |
| `offset` | `integer` | ✅ |  |


**Example:**

```json
{
  "data": [],
  "total": 0,
  "limit": 0,
  "offset": 0
}
```



### TemplateResponse

<a id="templateresponse"></a>

Schema for template response

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | `string (uuid)` | ✅ |  |
| `workspace_id` | `string (uuid)` | ✅ |  |
| `phone_number_id` | `string (uuid)` | ✅ |  |
| `name` | `string` | ✅ |  |
| `category` | `string` | ✅ |  |
| `language` | `string` | ✅ |  |
| `status` | `string` | ✅ |  |
| `meta_template_id` | `string (nullable)` | ✅ |  |
| `components` | `object` | ✅ |  |
| `rejection_reason` | `string (nullable)` | ✅ |  |
| `created_at` | `string` | ✅ |  |
| `updated_at` | `string` | ✅ |  |


**Example:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "name",
  "category": "category",
  "language": "language",
  "status": "status",
  "meta_template_id": "meta_template_id",
  "components": {},
  "rejection_reason": "rejection_reason",
  "created_at": "created_at",
  "updated_at": "updated_at"
}
```



### TemplateUpdate

<a id="templateupdate"></a>

Schema for updating template

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `components` | `object (nullable)` | ❌ |  |
| `status` | `string (nullable)` | ❌ |  |


**Example:**

```json
{
  "components": {},
  "status": "status"
}
```



### ValidationError

<a id="validationerror"></a>

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `loc` | `any[]` | ✅ |  |
| `msg` | `string` | ✅ |  |
| `type` | `string` | ✅ |  |


**Example:**

```json
{
  "loc": [],
  "msg": "msg",
  "type": "type"
}
```



### WorkspaceCreate

<a id="workspacecreate"></a>

Request model for creating a workspace

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | `string` | ✅ |  (minLength: 1, maxLength: 255) |
| `plan` | `WorkspacePlan` | ❌ |  Default: `free` |


**Example:**

```json
{
  "name": "name",
  "plan": "free"
}
```



### WorkspaceListResponse

<a id="workspacelistresponse"></a>

Summarized workspace info with user's role

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | `string (uuid)` | ✅ |  |
| `name` | `string` | ✅ |  |
| `slug` | `string` | ✅ |  |
| `plan` | `WorkspacePlan` | ✅ |  |
| `status` | `WorkspaceStatus` | ✅ |  |
| `created_at` | `string (date-time)` | ✅ |  |
| `user_role` | `MemberRole` | ✅ |  |


**Example:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "name",
  "slug": "slug",
  "plan": "free",
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z",
  "user_role": "OWNER"
}
```



### WorkspaceMemberResponse

<a id="workspacememberresponse"></a>

Response model for workspace member

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | `string (uuid)` | ✅ |  |
| `user_id` | `string (uuid)` | ✅ |  |
| `role` | `MemberRole` | ✅ |  |
| `status` | `MemberStatus` | ✅ |  |
| `joined_at` | `string (date-time) (nullable)` | ❌ |  |


**Example:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "OWNER",
  "status": "pending",
  "joined_at": "2024-01-01T00:00:00Z"
}
```



### WorkspacePlan

<a id="workspaceplan"></a>

**Enum Values:** `free | pro | enterprise`


### WorkspaceResponse

<a id="workspaceresponse"></a>

Full workspace response

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | `string (uuid)` | ✅ |  |
| `name` | `string` | ✅ |  |
| `slug` | `string` | ✅ |  |
| `api_key` | `string (uuid)` | ✅ |  |
| `webhook_secret` | `string (uuid)` | ✅ |  |
| `created_by` | `string (uuid)` | ✅ |  |
| `plan` | `WorkspacePlan` | ✅ |  |
| `status` | `WorkspaceStatus` | ✅ |  |
| `settings` | `object` | ✅ |  |
| `created_at` | `string (date-time)` | ✅ |  |
| `updated_at` | `string (date-time)` | ✅ |  |


**Example:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "name",
  "slug": "slug",
  "api_key": "550e8400-e29b-41d4-a716-446655440000",
  "webhook_secret": "550e8400-e29b-41d4-a716-446655440000",
  "created_by": "550e8400-e29b-41d4-a716-446655440000",
  "plan": "free",
  "status": "active",
  "settings": {},
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```



### WorkspaceStatus

<a id="workspacestatus"></a>

**Enum Values:** `active | suspended | cancelled`


### WorkspaceUpdate

<a id="workspaceupdate"></a>

Request model for updating a workspace

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | `string (nullable)` | ❌ |  |
| `plan` | `WorkspacePlan (nullable)` | ❌ |  |
| `status` | `WorkspaceStatus (nullable)` | ❌ |  |
| `settings` | `object (nullable)` | ❌ |  |


**Example:**

```json
{
  "name": "name",
  "plan": "{...}",
  "status": "{...}",
  "settings": {}
}
```
