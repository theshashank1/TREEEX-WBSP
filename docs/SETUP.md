# 🏠 Local Development Setup

This guide will help you set up the TREEEX-WBSP environment on your local machine for development and testing.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

1.  **Python 3.11+**: [Download Python](https://www.python.org/downloads/)
2.  **uv** (Recommended Package Manager):
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
3.  **PostgreSQL**: Local server or access to a cloud instance.
4.  **Redis**: Local server (`redis-server`) or cloud instance.
5.  **ngrok account**: [Sign up](https://ngrok.com/) (Required for local webhook testing).

---

## 🚀 Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/TREEEX-WBSP.git
cd TREEEX-WBSP
```

### 2. Configure Environment

Copy the example environment file and update it with your credentials.

```bash
cp .env.example server/.env
```

Open `server/.env` and configure at minimum:
- `DATABASE_URL`
- `REDIS_URL`
- `SUPABASE_URL` & `SUPABASE_KEY`
- `NGROK_AUTHTOKEN` (Get it from your ngrok dashboard)

See [Environment Variables Reference](ENVIRONMENT_VARIABLES.md) for full details.

### 3. Install Dependencies

We use `uv` for fast dependency management.

```bash
# Sync dependencies (creates virtualenv automatically)
uv sync

# Install development tools
uv pip install -e ".[dev]"
```

### 4. Initialize Database

Ensure your PostgreSQL server is running, then run migrations (if using Alembic) or allow the app to auto-create tables on startup (depending on configuration).

*(Note: If using `SQLModel` with `table=True`, tables are created automatically on app startup).*

---

## 🏃 Running the Application

For local development, you need to run three components: the API server (with ngrok) and background workers.

### Terminal 1: API Server + ngrok

This custom script starts the FastAPI server and automatically opens an ngrok tunnel pointing to it.

```bash
python run.py
```

> **Note:** You will see a public URL (e.g., `https://random-name.ngrok-free.app`) in the console. Use this URL to configure your Webhook in the Meta Developer Portal.

### Terminal 2: Outbound Worker

Handles message sending queue.

```bash
python -m server.workers.outbound
```

### Terminal 3: Webhook Worker

Handles incoming message processing.

```bash
python -m server.workers.webhook
```

---

## 🧪 Verifying Installation

1.  **Check Health Endpoint**:
    Open `http://localhost:8000/health` in your browser. You should see `{"status": "ok"}`.

2.  **Access Documentation**:
    Open `http://localhost:8000/docs` to see the Swagger UI.

3.  **Simulate Webhook**:
    If your ngrok tunnel is up, try sending a test event to `https://your-ngrok-url/webhooks`.

---

## 🐞 Common Issues

| Issue | Solution |
|:---|:---|
| **ModuleNotFoundError** | Ensure you are running with `uv run` or have activated the virtual environment (`.venv\Scripts\activate` on Windows). |
| **Connection Refused** | Check if Redis and PostgreSQL services are running. |
| **ngrok 401 Unauthorized** | Run `ngrok config add-authtoken <token>` or set `NGROK_AUTHTOKEN` in env. |
| **"Variables not set"** | Ensure you are editing `server/.env` and not just `.env.example`. |

Need more help? Check [Troubleshooting](TROUBLESHOOTING.md).
