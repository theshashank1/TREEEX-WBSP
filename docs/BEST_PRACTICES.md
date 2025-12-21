# 🛡️ Best Practices

Follow these guidelines to ensure security, reliability, and performance.

## 🔐 Security

### 1. Protect your Secrets
- **Never** commit `.env` files to git.
- Rotate `SECRET_KEY` and `SUPABASE_KEY` periodically.
- Don't expose the API directly to the internet; use a Reverse Proxy (Nginx).

### 2. Rate Limiting
- The API implements rate limiting, but you should also implement client-side backoff.
- Respect Meta's [Messaging Limits](https://developers.facebook.com/docs/whatsapp/messaging-limits).

### 3. Access Control
- Use strict Role-Based Access Control (RBAC) within workspaces.
- Only grant `ADMIN` privileges to trusted users.

---

## 🚀 Performance

### 1. Asynchronous Processing
- The API is designed to return quickly (`202 Accepted`) for message sending.
- Do not poll for status updates; rely on **Webhooks** or Real-time events.

### 2. Batching
- When importing contacts, use the Bulk Import API rather than creating contacts one by one.

### 3. Queue Management
- Monitor Redis memory usage (`redis-cli info memory`).
- Ensure Workers are running and healthy to process the backlog.

---

## 🏗️ Reliability

### 1. Idempotency
- The outbound worker handles duplicate requests gracefully.
- Ensure your webhook handler is also idempotent (Meta may send the same event twice).

### 2. Logging
- Use structural logging (JSON) in production for easier parsing.
- Monitor `logs/errors.log` for critical failures.
