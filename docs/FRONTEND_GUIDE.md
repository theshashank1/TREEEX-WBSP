# Quick Start Guide for Frontend Developers

## 🎯 Getting Started in 5 Minutes

### Step 1: Authentication

```javascript
// Store these in your environment variables
const API_BASE_URL = 'https://destined-severely-serval.ngrok-free.app';

// Sign up a new user
async function signup(email, password, name) {
  const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, name })
  });
  return await response.json();
}

// Sign in and get access token
async function signin(email, password) {
  const response = await fetch(`${API_BASE_URL}/api/auth/signin`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  const data = await response.json();
  // Store the access_token securely (localStorage/sessionStorage/cookie)
  localStorage.setItem('access_token', data.access_token);
  return data;
}

// Get current user
async function getCurrentUser(token) {
  const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return await response.json();
}
```

### Step 2: Create API Client

```javascript
// api-client.js
class APIClient {
  constructor(baseURL = 'https://destined-severely-serval.ngrok-free.app') {
    this.baseURL = baseURL;
  }

  getToken() {
    return localStorage.getItem('access_token');
  }

  async request(endpoint, options = {}) {
    const token = this.getToken();
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
      ...options,
      headers,
    };

    const response = await fetch(`${this.baseURL}${endpoint}`, config);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'API request failed');
    }

    return await response.json();
  }

  // Workspace methods
  async createWorkspace(name, plan = 'free') {
    return this.request('/api/workspaces', {
      method: 'POST',
      body: JSON.stringify({ name, plan })
    });
  }

  async listWorkspaces() {
    return this.request('/api/workspaces');
  }

  async getWorkspace(workspaceId) {
    return this.request(`/api/workspaces/${workspaceId}`);
  }

  // Phone number methods
  async registerPhoneNumber(data) {
    return this.request('/api/phone-numbers', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async listPhoneNumbers(workspaceId) {
    return this.request(`/api/phone-numbers?workspace_id=${workspaceId}`);
  }

  // Message methods
  async sendTextMessage(workspaceId, phoneNumberId, to, text) {
    return this.request('/api/messages/send/text', {
      method: 'POST',
      body: JSON.stringify({
        workspace_id: workspaceId,
        phone_number_id: phoneNumberId,
        to,
        text
      })
    });
  }

  async sendMediaMessage(workspaceId, phoneNumberId, to, mediaType, mediaId, caption) {
    return this.request('/api/messages/send/media', {
      method: 'POST',
      body: JSON.stringify({
        workspace_id: workspaceId,
        phone_number_id: phoneNumberId,
        to,
        media_type: mediaType,
        media_id: mediaId,
        caption
      })
    });
  }

  // Media methods
  async uploadMedia(workspaceId, file) {
    const formData = new FormData();
    formData.append('workspace_id', workspaceId);
    formData.append('file', file);

    const token = this.getToken();
    const response = await fetch(`${this.baseURL}/api/media`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    });

    if (!response.ok) {
      throw new Error('Media upload failed');
    }

    return await response.json();
  }

  async listMedia(workspaceId, type = null, limit = 20, offset = 0) {
    let query = `workspace_id=${workspaceId}&limit=${limit}&offset=${offset}`;
    if (type) query += `&type=${type}`;
    return this.request(`/api/media?${query}`);
  }

  // Contact methods
  async createContact(workspaceId, phoneNumber, name = null, tags = null) {
    return this.request('/api/contacts', {
      method: 'POST',
      body: JSON.stringify({
        workspace_id: workspaceId,
        phone_number: phoneNumber,
        name,
        tags
      })
    });
  }

  async listContacts(workspaceId, filters = {}) {
    const params = new URLSearchParams({
      workspace_id: workspaceId,
      ...filters
    });
    return this.request(`/api/contacts?${params}`);
  }

  async importContacts(workspaceId, file) {
    const formData = new FormData();
    formData.append('file', file);

    const token = this.getToken();
    const response = await fetch(
      `${this.baseURL}/api/contacts/import?workspace_id=${workspaceId}`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      }
    );

    if (!response.ok) {
      throw new Error('Contact import failed');
    }

    return await response.json();
  }

  // Campaign methods
  async createCampaign(workspaceId, phoneNumberId, name, templateId = null) {
    return this.request('/api/campaigns', {
      method: 'POST',
      body: JSON.stringify({
        workspace_id: workspaceId,
        phone_number_id: phoneNumberId,
        name,
        template_id: templateId
      })
    });
  }

  async listCampaigns(workspaceId, status = null) {
    let query = `workspace_id=${workspaceId}`;
    if (status) query += `&status=${status}`;
    return this.request(`/api/campaigns?${query}`);
  }

  async startCampaign(campaignId) {
    return this.request(`/api/campaigns/${campaignId}/start`, {
      method: 'POST'
    });
  }

  async pauseCampaign(campaignId) {
    return this.request(`/api/campaigns/${campaignId}/pause`, {
      method: 'POST'
    });
  }
}

// Export singleton instance
export const apiClient = new APIClient();
```

### Step 3: React Hooks (Optional)

```javascript
// hooks/useAPI.js
import { useState, useEffect } from 'react';
import { apiClient } from './api-client';

export function useWorkspaces() {
  const [workspaces, setWorkspaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchWorkspaces() {
      try {
        const data = await apiClient.listWorkspaces();
        setWorkspaces(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchWorkspaces();
  }, []);

  return { workspaces, loading, error };
}

export function useContacts(workspaceId, filters = {}) {
  const [contacts, setContacts] = useState({ data: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchContacts() {
      if (!workspaceId) return;

      try {
        setLoading(true);
        const data = await apiClient.listContacts(workspaceId, filters);
        setContacts(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchContacts();
  }, [workspaceId, JSON.stringify(filters)]);

  return { contacts, loading, error };
}
```

## 📱 Common Use Cases

### Use Case 1: Send a Simple Text Message

```javascript
import { apiClient } from './api-client';

async function sendWelcomeMessage() {
  try {
    const result = await apiClient.sendTextMessage(
      'workspace-uuid-here',
      'phone-number-uuid-here',
      '+1234567890',
      'Welcome to our service!'
    );
    console.log('Message sent:', result);
  } catch (error) {
    console.error('Failed to send message:', error);
  }
}
```

### Use Case 2: Upload and Send Image

```javascript
async function sendImageMessage(imageFile, caption) {
  try {
    // Step 1: Upload the image
    const mediaResult = await apiClient.uploadMedia(
      'workspace-uuid-here',
      imageFile
    );

    // Step 2: Send the media message
    const messageResult = await apiClient.sendMediaMessage(
      'workspace-uuid-here',
      'phone-number-uuid-here',
      '+1234567890',
      'image',
      mediaResult.id,
      caption
    );

    console.log('Image message sent:', messageResult);
  } catch (error) {
    console.error('Failed to send image:', error);
  }
}
```

### Use Case 3: Import Contacts from CSV

```javascript
async function handleContactImport(file) {
  try {
    const result = await apiClient.importContacts(
      'workspace-uuid-here',
      file
    );

    console.log(`Imported: ${result.imported}`);
    console.log(`Updated: ${result.updated}`);
    console.log(`Failed: ${result.failed}`);

    // Show detailed results
    result.results.forEach(row => {
      if (row.status === 'failed') {
        console.error(`Row ${row.row_number}: ${row.reason}`);
      }
    });
  } catch (error) {
    console.error('Import failed:', error);
  }
}
```

### Use Case 4: Create and Start a Campaign

```javascript
async function launchCampaign() {
  try {
    // Step 1: Create the campaign
    const campaign = await apiClient.createCampaign(
      'workspace-uuid-here',
      'phone-number-uuid-here',
      'Summer Sale Campaign',
      'template-uuid-here' // optional
    );

    console.log('Campaign created:', campaign.id);

    // Step 2: Start the campaign
    const started = await apiClient.startCampaign(campaign.id);
    console.log('Campaign status:', started.status);

  } catch (error) {
    console.error('Campaign failed:', error);
  }
}
```

## 🎨 UI Component Examples

### Login Form (React)

```jsx
import { useState } from 'react';
import { apiClient } from './api-client';

function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const data = await fetch('https://destined-severely-serval.ngrok-free.app/api/auth/signin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      }).then(r => r.json());

      localStorage.setItem('access_token', data.access_token);
      window.location.href = '/dashboard';
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={e => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <input
        type="password"
        value={password}
        onChange={e => setPassword(e.target.value)}
        placeholder="Password"
        required
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Signing in...' : 'Sign In'}
      </button>
      {error && <div className="error">{error}</div>}
    </form>
  );
}
```

### Send Message Form

```jsx
import { useState } from 'react';
import { apiClient } from './api-client';

function SendMessageForm({ workspaceId, phoneNumberId }) {
  const [recipient, setRecipient] = useState('');
  const [message, setMessage] = useState('');
  const [status, setStatus] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setStatus('sending');

    try {
      await apiClient.sendTextMessage(
        workspaceId,
        phoneNumberId,
        recipient,
        message
      );
      setStatus('sent');
      setMessage('');
      setRecipient('');
    } catch (error) {
      setStatus('error');
      console.error(error);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="tel"
        value={recipient}
        onChange={e => setRecipient(e.target.value)}
        placeholder="+1234567890"
        required
      />
      <textarea
        value={message}
        onChange={e => setMessage(e.target.value)}
        placeholder="Type your message..."
        required
      />
      <button type="submit" disabled={status === 'sending'}>
        Send Message
      </button>
      {status === 'sent' && <div>✅ Message sent!</div>}
      {status === 'error' && <div>❌ Failed to send</div>}
    </form>
  );
}
```

## 🔧 Error Handling

```javascript
async function handleAPICall() {
  try {
    const result = await apiClient.sendTextMessage(...);
    // Success
  } catch (error) {
    // Handle different error types
    if (error.message.includes('401')) {
      // Unauthorized - redirect to login
      window.location.href = '/login';
    } else if (error.message.includes('403')) {
      // Forbidden - show permission error
      alert('You do not have permission to perform this action');
    } else if (error.message.includes('404')) {
      // Not found
      alert('Resource not found');
    } else if (error.message.includes('422')) {
      // Validation error
      alert('Please check your input');
    } else {
      // General error
      alert('An error occurred. Please try again.');
    }
  }
}
```

## 📊 Pagination Example

```javascript
function ContactList({ workspaceId }) {
  const [contacts, setContacts] = useState([]);
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const limit = 20;

  async function loadContacts(pageNum) {
    const offset = pageNum * limit;
    const data = await apiClient.listContacts(workspaceId, {
      limit,
      offset
    });

    setContacts(data.data);
    setTotal(data.total);
    setPage(pageNum);
  }

  useEffect(() => {
    loadContacts(0);
  }, [workspaceId]);

  const totalPages = Math.ceil(total / limit);

  return (
    <div>
      <ul>
        {contacts.map(contact => (
          <li key={contact.id}>{contact.name || contact.phone_number}</li>
        ))}
      </ul>

      <div>
        <button
          onClick={() => loadContacts(page - 1)}
          disabled={page === 0}
        >
          Previous
        </button>

        <span>Page {page + 1} of {totalPages}</span>

        <button
          onClick={() => loadContacts(page + 1)}
          disabled={page >= totalPages - 1}
        >
          Next
        </button>
      </div>
    </div>
  );
}
```

## 🌐 Environment Variables

Create a `.env` file in your frontend project:

```env
VITE_API_BASE_URL=https://destined-severely-serval.ngrok-free.app
VITE_API_TIMEOUT=30000
```

Use in your code:

```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://destined-severely-serval.ngrok-free.app';
```

## 🚨 Important Notes

1. **Phone Numbers**: Must be in E.164 format (e.g., `+1234567890`)
2. **UUIDs**: All IDs are UUIDs, not integers
3. **Authentication**: Token expires after some time, implement refresh logic
4. **File Upload**: Use `FormData` for file uploads (media, contact imports)
5. **CORS**: Ensure CORS is configured on the backend for your frontend domain

## 🎯 Next Steps

1. Review the complete API reference in `API_REFERENCE.md`
2. Set up error boundary in your React app
3. Implement token refresh logic
4. Add request/response interceptors for logging
5. Consider using React Query or SWR for better data fetching

## 📞 Need Help?

- Check `API_REFERENCE.md` for detailed endpoint documentation
- Review `README.md` for API overview
- Contact backend team for support
