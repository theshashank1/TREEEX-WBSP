"""
Outbound Messaging Tests - tests/test_outbound.py

Unit and integration tests for the WhatsApp outbound messaging system.

Run with: python -m pytest tests/test_outbound.py -v
"""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from server.core.rate_limiter import TokenBucket, TokenBucketRateLimiter
from server.schemas.outbound import (
    Button,
    InteractiveButtonsMessage,
    MediaMessage,
    TextMessage,
    parse_outbound_message,
)
from server.whatsapp.outbound import MetaAPIError, OutboundClient, SendResult

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_access_token():
    return "test_access_token_12345"


@pytest.fixture
def mock_phone_number_id():
    return "123456789012345"


@pytest.fixture
def outbound_client(mock_access_token, mock_phone_number_id):
    return OutboundClient(
        access_token=mock_access_token,
        phone_number_id=mock_phone_number_id,
    )


# =============================================================================
# SCHEMA VALIDATION TESTS
# =============================================================================


class TestMessageSchemas:
    """Test Pydantic schema validation."""

    def test_text_message_valid(self):
        """Test valid text message schema."""
        data = {
            "type": "text_message",
            "message_id": str(uuid.uuid4()),
            "workspace_id": str(uuid.uuid4()),
            "phone_number_id": "123456789",
            "to_number": "+15551234567",
            "text": "Hello, World!",
            "preview_url": True,
        }
        msg = parse_outbound_message(data)
        assert isinstance(msg, TextMessage)
        assert msg.text == "Hello, World!"
        assert msg.preview_url is True

    def test_text_message_invalid_phone(self):
        """Test text message with invalid phone number."""
        data = {
            "type": "text_message",
            "message_id": str(uuid.uuid4()),
            "workspace_id": str(uuid.uuid4()),
            "phone_number_id": "123456789",
            "to_number": "not-a-phone",
            "text": "Hello",
        }
        with pytest.raises(ValueError):
            parse_outbound_message(data)

    def test_interactive_buttons_valid(self):
        """Test valid interactive buttons message."""
        data = {
            "type": "interactive_buttons",
            "message_id": str(uuid.uuid4()),
            "workspace_id": str(uuid.uuid4()),
            "phone_number_id": "123456789",
            "to_number": "+15551234567",
            "body_text": "Would you like to proceed?",
            "buttons": [
                {"id": "yes", "title": "Yes"},
                {"id": "no", "title": "No"},
            ],
        }
        msg = parse_outbound_message(data)
        assert isinstance(msg, InteractiveButtonsMessage)
        assert len(msg.buttons) == 2

    def test_interactive_buttons_too_many(self):
        """Test interactive buttons with more than 3 buttons fails."""
        data = {
            "type": "interactive_buttons",
            "message_id": str(uuid.uuid4()),
            "workspace_id": str(uuid.uuid4()),
            "phone_number_id": "123456789",
            "to_number": "+15551234567",
            "body_text": "Choose one",
            "buttons": [
                {"id": "1", "title": "One"},
                {"id": "2", "title": "Two"},
                {"id": "3", "title": "Three"},
                {"id": "4", "title": "Four"},  # Too many!
            ],
        }
        with pytest.raises(ValueError):
            parse_outbound_message(data)

    def test_media_message_valid(self):
        """Test valid media message with URL."""
        data = {
            "type": "media_message",
            "message_id": str(uuid.uuid4()),
            "workspace_id": str(uuid.uuid4()),
            "phone_number_id": "123456789",
            "to_number": "+15551234567",
            "media_type": "image",
            "media_url": "https://example.com/image.jpg",
            "caption": "Check this out!",
        }
        msg = parse_outbound_message(data)
        assert isinstance(msg, MediaMessage)
        assert msg.media_type == "image"

    def test_media_message_no_source(self):
        """Test media message without URL or ID fails."""
        data = {
            "type": "media_message",
            "message_id": str(uuid.uuid4()),
            "workspace_id": str(uuid.uuid4()),
            "phone_number_id": "123456789",
            "to_number": "+15551234567",
            "media_type": "image",
            # No media_url or media_id!
        }
        with pytest.raises(ValueError):
            parse_outbound_message(data)

    def test_unknown_message_type(self):
        """Test unknown message type raises error."""
        data = {
            "type": "unknown_type",
            "message_id": str(uuid.uuid4()),
        }
        with pytest.raises(ValueError, match="Unknown message type"):
            parse_outbound_message(data)


# =============================================================================
# OUTBOUND CLIENT TESTS
# =============================================================================


class TestOutboundClient:
    """Test OutboundClient methods."""

    @pytest.mark.asyncio
    async def test_send_text_message_success(self, outbound_client):
        """Test successful text message send."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"messages": [{"id": "wamid.test123"}]}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await outbound_client.send_text_message(
                to_number="+15551234567",
                text="Hello, World!",
            )

            assert result.success
            assert result.wa_message_id == "wamid.test123"
            assert result.error is None

    @pytest.mark.asyncio
    async def test_send_text_message_rate_limited(self, outbound_client):
        """Test rate limit error is marked as retryable."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            "error": {
                "code": 130429,
                "message": "Rate limit exceeded",
            }
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await outbound_client.send_text_message(
                to_number="+15551234567",
                text="Hello",
            )

            assert not result.success
            assert result.error is not None
            assert result.error.is_retryable is True

    @pytest.mark.asyncio
    async def test_send_text_message_invalid_number(self, outbound_client):
        """Test invalid phone number error is not retryable."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {
                "code": 100,
                "message": "Invalid phone number",
            }
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await outbound_client.send_text_message(
                to_number="+15551234567",
                text="Hello",
            )

            assert not result.success
            assert result.error.is_retryable is False

    @pytest.mark.asyncio
    async def test_send_interactive_buttons(self, outbound_client):
        """Test sending interactive buttons."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"messages": [{"id": "wamid.buttons123"}]}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await outbound_client.send_interactive_buttons(
                to_number="+15551234567",
                body_text="Choose an option",
                buttons=[
                    {"id": "yes", "title": "Yes"},
                    {"id": "no", "title": "No"},
                ],
            )

            assert result.success
            assert result.wa_message_id == "wamid.buttons123"

            # Verify payload structure
            call_kwargs = mock_post.call_args
            payload = call_kwargs.kwargs["json"]
            assert payload["type"] == "interactive"
            assert payload["interactive"]["type"] == "button"

    @pytest.mark.asyncio
    async def test_send_template_message(self, outbound_client):
        """Test sending template message."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"messages": [{"id": "wamid.template123"}]}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await outbound_client.send_template_message(
                to_number="+15551234567",
                template_name="hello_world",
                language_code="en",
            )

            assert result.success

            payload = mock_post.call_args.kwargs["json"]
            assert payload["type"] == "template"
            assert payload["template"]["name"] == "hello_world"

    @pytest.mark.asyncio
    async def test_send_media_message(self, outbound_client):
        """Test sending media message."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"messages": [{"id": "wamid.image123"}]}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await outbound_client.send_media_message(
                to_number="+15551234567",
                media_type="image",
                media_url="https://example.com/image.jpg",
                caption="Check this out!",
            )

            assert result.success

            payload = mock_post.call_args.kwargs["json"]
            assert payload["type"] == "image"
            assert payload["image"]["link"] == "https://example.com/image.jpg"


# =============================================================================
# RATE LIMITER TESTS
# =============================================================================


class TestRateLimiter:
    """Test TokenBucketRateLimiter."""

    def test_token_bucket_consume(self):
        """Test basic token consumption."""
        bucket = TokenBucket(capacity=10, refill_rate=10, tokens=10)

        # Should consume successfully
        assert bucket.consume(5) is True
        assert bucket.tokens == 5

        # Should consume remaining
        assert bucket.consume(5) is True
        assert bucket.tokens == 0

        # Should fail - no tokens
        assert bucket.consume(1) is False

    def test_token_bucket_refill(self):
        """Test token refill over time."""
        bucket = TokenBucket(capacity=10, refill_rate=100, tokens=0)

        # Simulate time passage
        import time

        bucket.last_refill = time.monotonic() - 0.1  # 100ms ago
        bucket.refill()

        # Should have refilled ~10 tokens (100 tokens/sec * 0.1 sec)
        assert bucket.tokens >= 9  # Allow some tolerance

    @pytest.mark.asyncio
    async def test_rate_limiter_acquire(self):
        """Test rate limiter acquire."""
        limiter = TokenBucketRateLimiter(capacity=5, refill_rate=5)

        # Should acquire successfully
        assert await limiter.acquire("test_key") is True
        assert await limiter.acquire("test_key") is True

        # Exhaust tokens
        for _ in range(3):
            await limiter.acquire("test_key")

        # Should fail
        assert await limiter.acquire("test_key") is False

    @pytest.mark.asyncio
    async def test_rate_limiter_per_key(self):
        """Test rate limiting is per-key."""
        limiter = TokenBucketRateLimiter(capacity=2, refill_rate=1)

        # Exhaust key1
        assert await limiter.acquire("key1") is True
        assert await limiter.acquire("key1") is True
        assert await limiter.acquire("key1") is False

        # key2 should still work
        assert await limiter.acquire("key2") is True

    @pytest.mark.asyncio
    async def test_rate_limiter_wait(self):
        """Test waiting for token."""
        limiter = TokenBucketRateLimiter(capacity=1, refill_rate=100)  # Fast refill

        # Exhaust
        await limiter.acquire("test")

        # Wait should succeed quickly
        result = await limiter.wait_for_token("test", timeout=1.0)
        assert result is True


# =============================================================================
# INTEGRATION TESTS (require Redis mock)
# =============================================================================


class TestWorkerIntegration:
    """Integration tests for worker processing."""

    @pytest.mark.asyncio
    async def test_idempotency_check(self):
        """Test idempotency prevents duplicate sends."""
        from server.workers.outbound import check_already_sent, mark_as_sent

        message_id = str(uuid.uuid4())

        with patch(
            "server.workers.outbound.cache_get", new_callable=AsyncMock
        ) as mock_get:
            with patch(
                "server.workers.outbound.cache_set", new_callable=AsyncMock
            ) as mock_set:
                # First check - not sent yet
                mock_get.return_value = None
                assert await check_already_sent(message_id) is False

                # Mark as sent
                await mark_as_sent(message_id, "wamid.123")
                mock_set.assert_called_once()

                # Second check - already sent
                mock_get.return_value = "wamid.123"
                assert await check_already_sent(message_id) is True

    def test_backoff_calculation(self):
        """Test exponential backoff calculation."""
        from server.workers.outbound import calculate_backoff

        # First attempt
        delay1 = calculate_backoff(1, base_delay=1.0, max_delay=60.0, jitter_factor=0)
        assert delay1 == 1.0

        # Second attempt (2^1 = 2)
        delay2 = calculate_backoff(2, base_delay=1.0, max_delay=60.0, jitter_factor=0)
        assert delay2 == 2.0

        # Third attempt (2^2 = 4)
        delay3 = calculate_backoff(3, base_delay=1.0, max_delay=60.0, jitter_factor=0)
        assert delay3 == 4.0

        # Should cap at max
        delay_max = calculate_backoff(
            10, base_delay=1.0, max_delay=60.0, jitter_factor=0
        )
        assert delay_max == 60.0

    def test_backoff_with_jitter(self):
        """Test backoff includes jitter."""
        from server.workers.outbound import calculate_backoff

        # With 50% jitter, delay should vary
        delays = [
            calculate_backoff(1, base_delay=10.0, max_delay=60.0, jitter_factor=0.5)
            for _ in range(10)
        ]

        # All delays should be between 5 and 15 (10 ± 50%)
        for delay in delays:
            assert 5.0 <= delay <= 15.0

        # Should not all be identical (very unlikely with jitter)
        assert len(set(delays)) > 1


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
