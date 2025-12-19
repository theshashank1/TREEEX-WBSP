# TREEEX WhatsApp BSP

A robust WhatsApp Business Solution Provider (BSP) platform built with FastAPI, designed for scale and developer experience.

## 🚀 Features

- **FastAPI Core**: High-performance asynchronous API.
- **Supabase Integration**: Seamless authentication and database management.
- **Meta WhatsApp Graph API**: Complete integration for messaging, templates, and webhooks.
- **Automated Tunneling**: Built-in ngrok integration for easy local development and webhook testing.
- **Redis Caching**: Optimized performance for message tracking and rate limiting.
- **Azure Storage**: Scalable media handling.

## 🛠️ Setup

### Prerequisites

- [Python 3.12+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/) (Recommended package manager)
- [ngrok](https://ngrok.com/) account (for webhooks)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd TREEEX-WBSP
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the project root and fill in your credentials (see `server/env.txt` for a template):
   ```bash
   # Essential Variables
   SUPABASE_URL=...
   SUPABASE_SECRET_KEY=...
   NGROK_AUTHTOKEN=...
   DATABASE_URL=...
   ```

## 🏃 Running the Server

To start the server with an automated ngrok tunnel (perfect for WhatsApp webhooks):

```bash
python run.py
```

This will:
1. Initialize a ngrok tunnel (on your static domain if configured).
2. Start the FastAPI server with hot-reload enabled.
3. Provide a public URL like `https://destined-severely-serval.ngrok-free.app`.

### Monitoring
- **API Dashboard**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Ngrok Dashboard**: [http://localhost:4040](http://localhost:4040)

## 📁 Project Structure

- `server/api/`: API route definitions (auth, campaigns, webhooks, etc.).
- `server/core/`: Core configurations (database, redis, supabase).
- `server/models/`: SQLAlchemy database models.
- `server/schemas/`: Pydantic models for request/response validation.
- `run.py`: Development entry point with ngrok integration.

## 🗄️ Database

Connect to the Azure PostgreSQL database:
```bash
psql "postgresql://theshashank1:<password>@treeex.postgres.database.azure.com:5432/postgres"
```

---
Built with ❤️ for the TREEEX ecosystem.
