# Environment Variables Reference

A complete reference for all environment variables used in TREEEX-WBSP.

## ⚙️ Core Configuration

These variables are required for the application to start.

| Variable | Description | Default | Required |
|:---|:---|:---|:---:|
| `ENV` | Application environment (`development`, `production`, `testing`) | `development` | ✅ |
| `DEBUG` | Enable debug mode (detailed errors, auto-reload) | `false` | ❌ |
| `SECRET_KEY` | Secret key for cryptographic signing (JWT) | - | ✅ |
| `HOST` | Server host IP | `0.0.0.0` | ❌ |
| `PORT` | Server port | `8000` | ❌ |

## 🗄️ Database (PostgreSQL)

| Variable | Description | Example |
|:---|:---|:---|
| `DATABASE_URL` | Full SQLAlchemy connection string | `postgresql://user:pass@host/db` |

_Alternatively, use individual components:_
`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`

## 🔐 Authentication (Supabase)

| Variable | Description | Required |
|:---|:---|:---:|
| `SUPABASE_URL` | Project URL from Supabase Settings | ✅ |
| `SUPABASE_KEY` | Public Anon Key or Service Role Key | ✅ |

## 🚀 Messaging (Redis)

| Variable | Description | Default |
|:---|:---|:---|
| `REDIS_URL` | Connection URL for Redis | `redis://localhost:6379` |

## 💬 WhatsApp Meta API

Required for sending and receiving messages.

| Variable | Description | Where to find it |
|:---|:---|:---|
| `META_ACCESS_TOKEN` | System User Access Token | Meta Business Settings |
| `META_APP_SECRET` | App Secret | App Basic Settings |
| `META_WEBHOOK_VERIFY_TOKEN` | Custom token for webhook verification | You define this |
| `META_GRAPH_API_URL` | Graph API Base URL | `https://graph.facebook.com` |
| `META_API_VERSION` | API Version (e.g., `v18.0`) | `v18.0` |

## ☁️ Media Storage (Azure)

| Variable | Description |
|:---|:---|
| `AZURE_STORAGE_CONNECTION_STRING` | Full connection string |
| `AZURE_STORAGE_CONTAINER_NAME` | Container name for media |

## 🛠️ Development Tools

| Variable | Description |
|:---|:---|
| `NGROK_AUTHTOKEN` | Auth token for ngrok tunnelling |
| `NGROK_DOMAIN` | Static domain (optional) |

## 🛡️ Security & Limits

| Variable | Description | Default |
|:---|:---|:---|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT Token expiry | `10080` (7 days) |
| `RATE_LIMIT_MESSAGES_PER_SECOND` | Global message sending rate | `10` |
