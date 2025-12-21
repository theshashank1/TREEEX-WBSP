"""
Test configuration and shared fixtures.

This module provides common test fixtures for the TREEEX-WBSP test suite.
"""

from __future__ import annotations

import uuid
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

# =============================================================================
# FIXTURES: IDs and Tokens
# =============================================================================


@pytest.fixture
def workspace_id() -> str:
    """Generate a random workspace UUID."""
    return str(uuid.uuid4())


@pytest.fixture
def user_id() -> str:
    """Generate a random user UUID."""
    return str(uuid.uuid4())


@pytest.fixture
def phone_number_id() -> str:
    """Meta phone number ID (numeric string)."""
    return "123456789012345"


@pytest.fixture
def message_id() -> str:
    """Generate a random message UUID."""
    return str(uuid.uuid4())


@pytest.fixture
def access_token() -> str:
    """Mock Meta access token."""
    return "test_access_token_12345"


# =============================================================================
# FIXTURES: Mock Clients
# =============================================================================


@pytest.fixture
def mock_redis() -> Generator[MagicMock, None, None]:
    """Mock Redis client for queue operations."""
    with patch("server.core.redis.get_redis") as mock:
        redis_mock = AsyncMock()
        mock.return_value = redis_mock
        yield redis_mock


@pytest.fixture
def mock_outbound_client() -> Generator[MagicMock, None, None]:
    """Mock WhatsApp outbound client."""
    with patch("server.whatsapp.outbound.OutboundClient") as mock:
        yield mock


@pytest.fixture
def mock_httpx_client() -> Generator[AsyncMock, None, None]:
    """Mock httpx async client for HTTP requests."""
    with patch("httpx.AsyncClient") as mock:
        client = AsyncMock()
        mock.return_value.__aenter__.return_value = client
        yield client


# =============================================================================
# FIXTURES: Database Session
# =============================================================================


@pytest_asyncio.fixture
async def mock_session() -> AsyncGenerator[AsyncMock, None]:
    """Mock async database session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    yield session


# =============================================================================
# FIXTURES: Sample Data
# =============================================================================


@pytest.fixture
def sample_text_message(
    workspace_id: str, phone_number_id: str, message_id: str
) -> dict:
    """Sample text message payload for queue."""
    return {
        "type": "text_message",
        "message_id": message_id,
        "workspace_id": workspace_id,
        "phone_number_id": phone_number_id,
        "to_number": "+15551234567",
        "text": "Hello from tests!",
        "preview_url": False,
    }


@pytest.fixture
def sample_template_message(
    workspace_id: str, phone_number_id: str, message_id: str
) -> dict:
    """Sample template message payload for queue."""
    return {
        "type": "template_message",
        "message_id": message_id,
        "workspace_id": workspace_id,
        "phone_number_id": phone_number_id,
        "to_number": "+15551234567",
        "template_name": "hello_world",
        "language_code": "en",
        "components": [],
    }


@pytest.fixture
def sample_webhook_message() -> dict:
    """Sample incoming webhook message from Meta."""
    return {
        "type": "message",
        "phone_number_id": "123456789",
        "from": "15551234567",
        "wa_id": "15551234567",
        "timestamp": "1640000000",
        "message_id": "wamid.test123",
        "message_type": "text",
        "message": {"text": {"body": "Hello from user!"}},
    }


@pytest.fixture
def sample_status_webhook() -> dict:
    """Sample status update webhook from Meta."""
    return {
        "type": "status",
        "phone_number_id": "123456789",
        "wa_message_id": "wamid.test123",
        "status": "delivered",
        "timestamp": "1640000000",
        "recipient_id": "15551234567",
    }


# =============================================================================
# FIXTURES: HTTP Response Mocks
# =============================================================================


@pytest.fixture
def meta_success_response() -> MagicMock:
    """Mock successful Meta API response."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"messages": [{"id": "wamid.success123"}]}
    return response


@pytest.fixture
def meta_rate_limit_response() -> MagicMock:
    """Mock rate-limited Meta API response."""
    response = MagicMock()
    response.status_code = 429
    response.json.return_value = {
        "error": {"code": 130429, "message": "Rate limit exceeded"}
    }
    return response


@pytest.fixture
def meta_error_response() -> MagicMock:
    """Mock failed Meta API response."""
    response = MagicMock()
    response.status_code = 400
    response.json.return_value = {
        "error": {"code": 100, "message": "Invalid phone number format"}
    }
    return response
