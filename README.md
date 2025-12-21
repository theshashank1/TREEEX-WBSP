# TREEEX WhatsApp BSP

A robust WhatsApp Business Solution Provider (BSP) platform built with FastAPI, designed for scale and developer experience.

## 🚀 Features

- **FastAPI Core**: High-performance asynchronous API
- **Supabase Integration**: Seamless authentication and database management
- **Meta WhatsApp Graph API**: Complete integration for messaging, templates, and webhooks
- **Automated Tunneling**: Built-in ngrok integration for local development
- **Redis Queues**: Reliable message queue with retry logic
- **Azure Storage**: Scalable media handling

## 🛠️ Setup

### Prerequisites

- [Python 3.11+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/) (Recommended package manager)
- [ngrok](https://ngrok.com/) account (for webhooks)
- Redis server
- PostgreSQL database

### Installation

```bash
git clone <repository-url>
cd TREEEX-WBSP

# Install dependencies
uv sync

# Install dev dependencies (for testing)
uv pip install -e ".[dev]"

# Configure environment
cp .env.example server/.env
# Edit server/.env with your credentials
```

## 🏃 Running

### API Server

```bash
# With ngrok tunnel (recommended for development)
python run.py

# Without ngrok
uvicorn server.main:app --reload
```

### Background Workers

Workers are required for processing messages:

```bash
# Terminal 1: Outbound message worker
python -m server.workers.outbound

# Terminal 2: Webhook processing worker
python -m server.workers.webhook
```

### Health Checks

- **Health**: `GET /health` - Service running check
- **Ready**: `GET /ready` - Ready to accept traffic
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

## 📁 Project Structure

```
TREEEX-WBSP/
├── server/
│   ├── api/          # API route handlers
│   ├── core/         # Config, database, Redis
│   ├── models/       # SQLAlchemy/SQLModel models
│   ├── schemas/      # Pydantic request/response schemas
│   ├── services/     # Azure storage, business logic
│   ├── workers/      # Background job processors
│   └── whatsapp/     # WhatsApp API client
├── tests/            # Test suite
├── docs/             # API documentation
└── run.py            # Dev entry point with ngrok
```

## 🧪 Testing

```bash
python -m pytest tests/ -v
```

## 📖 Documentation

- [API Reference](docs/API_REFERENCE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Frontend Guide](docs/FRONTEND_GUIDE.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](docs/CHANGELOG.md)

## 🔧 Troubleshooting

### Common Issues

**Ngrok not connecting:**
- Ensure `NGROK_AUTHTOKEN` is set in your `.env` file
- Check if another ngrok instance is running

**Workers not processing:**
- Verify Redis is running and `REDIS_URL` is correct
- Check worker terminal for error messages

**Database errors:**
- Verify `DATABASE_URL` is correct
- Ensure PostgreSQL server is accessible

---
Built with ❤️ for the TREEEX ecosystem.
