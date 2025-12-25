# Changelog

All notable changes to TREEEX-WBSP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Health check endpoints (`/health`, `/ready`) for container orchestration
- CORS middleware configuration for frontend integration
- `.env.example` template with all configuration options
- `CONTRIBUTING.md` contributor guidelines
- pytest and pytest-asyncio dev dependencies
- NGROK_AUTHTOKEN and NGROK_DOMAIN environment variable support
- **`server/whatsapp/renderer.py`** - Command → dict converter
- **`tests/test_renderer.py`** - 12 unit tests for renderer

### Changed
- **Messaging architecture**: Command → Renderer → dict → Client flow
- `server/workers/outbound.py` - Simplified from 90 lines to 18 lines
- `server/workers/campaign.py` - Now uses Pydantic `TemplateMessage` commands
- `server/whatsapp/outbound.py` - Added `send_payload()` method

### Changed
- Moved test files from root to `tests/` directory
- Updated `pyproject.toml` with proper metadata and keywords
- Improved FastAPI app configuration with title, description, version
- Removed hardcoded ngrok credentials from `run.py`

### Security
- Fixed hardcoded ngrok authtoken exposure in `run.py`

## [0.1.0] - 2024-12-21

### Added
- Initial WhatsApp Business Solution Provider API
- Authentication with Supabase
- Workspace and phone number management
- Text, template, and media message sending
- Webhook handling for incoming messages
- Redis-based message queue with outbound worker
- Azure Blob Storage for media files
- Rate limiting support
- Comprehensive API documentation
