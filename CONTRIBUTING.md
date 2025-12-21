# Contributing to TREEEX-WBSP

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Redis (for message queues)
- PostgreSQL database

### Installation

1. Clone and install dependencies:
   ```bash
   git clone <repository-url>
   cd TREEEX-WBSP
   uv sync
   uv pip install -e ".[dev]"
   ```

2. Copy environment template:
   ```bash
   cp .env.example server/.env
   # Edit server/.env with your credentials
   ```

3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Running the Application

### API Server
```bash
python run.py        # With ngrok tunnel
# OR
uvicorn server.main:app --reload  # Local only
```

### Workers
```bash
python -m server.workers.outbound    # Message sending
python -m server.workers.webhook     # Webhook processing
```

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_outbound.py -v
```

## Code Style

We use pre-commit hooks for consistent formatting:

- **ruff** - Linting and formatting
- **black** - Code formatting (via ruff)

Hooks run automatically on commit. To run manually:
```bash
pre-commit run --all-files
```

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with tests
3. Ensure all tests pass
4. Submit PR with clear description

## Project Structure

```
TREEEX-WBSP/
├── server/
│   ├── api/        # API route handlers
│   ├── core/       # Config, DB, Redis
│   ├── models/     # SQLAlchemy models
│   ├── schemas/    # Pydantic schemas
│   ├── services/   # Business logic
│   ├── workers/    # Background workers
│   └── whatsapp/   # WhatsApp API client
├── tests/          # Test suite
└── docs/           # Documentation
```
