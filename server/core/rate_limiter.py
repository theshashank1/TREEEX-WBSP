"""
Token Bucket Rate Limiter - server/core/rate_limiter.py

Async token bucket rate limiter for controlling API request rates.
Used by the outbound worker to respect WhatsApp API limits.

WhatsApp Cloud API limits:
- ~80 messages/second per phone number (tier dependent)
- Burst capacity for short spikes
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

from server.core.monitoring import log_event


@dataclass
class TokenBucket:
    """Token bucket for a single key (e.g., phone_number_id)."""

    capacity: float  # Maximum tokens
    refill_rate: float  # Tokens per second
    tokens: float = field(default=0)  # Current tokens
    last_refill: float = field(default_factory=time.monotonic)

    def refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

    def consume(self, tokens: float = 1) -> bool:
        """
        Try to consume tokens.

        Returns:
            True if tokens were consumed, False if insufficient tokens
        """
        self.refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def wait_time(self, tokens: float = 1) -> float:
        """
        Calculate time to wait for sufficient tokens.

        Returns:
            Seconds to wait (0 if tokens available now)
        """
        self.refill()
        if self.tokens >= tokens:
            return 0
        needed = tokens - self.tokens
        return needed / self.refill_rate


class TokenBucketRateLimiter:
    """
    Async token bucket rate limiter with per-key buckets.

    Usage:
        limiter = TokenBucketRateLimiter(
            capacity=80,  # Burst capacity
            refill_rate=80,  # 80 tokens/second
        )

        # Non-blocking check
        if await limiter.acquire("phone_123"):
            # Send message
        else:
            # Rate limited

        # Blocking wait
        await limiter.wait_for_token("phone_123", timeout=30)
        # Send message
    """

    def __init__(
        self,
        capacity: float = 80,
        refill_rate: float = 80,
        global_capacity: Optional[float] = None,
        global_refill_rate: Optional[float] = None,
    ):
        """
        Initialize rate limiter.

        Args:
            capacity: Per-key bucket capacity (burst limit)
            refill_rate: Per-key token refill rate (tokens/second)
            global_capacity: Optional global rate limit capacity
            global_refill_rate: Optional global rate limit refill rate
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.buckets: Dict[str, TokenBucket] = {}
        self._lock = asyncio.Lock()

        # Optional global limiter
        self.global_bucket: Optional[TokenBucket] = None
        if global_capacity and global_refill_rate:
            self.global_bucket = TokenBucket(
                capacity=global_capacity,
                refill_rate=global_refill_rate,
                tokens=global_capacity,
            )

    def _get_bucket(self, key: str) -> TokenBucket:
        """Get or create bucket for key."""
        if key not in self.buckets:
            self.buckets[key] = TokenBucket(
                capacity=self.capacity,
                refill_rate=self.refill_rate,
                tokens=self.capacity,  # Start full
            )
        return self.buckets[key]

    async def acquire(self, key: str, tokens: float = 1) -> bool:
        """
        Try to acquire tokens for a key (non-blocking).

        Args:
            key: Rate limit key (e.g., phone_number_id)
            tokens: Number of tokens to acquire

        Returns:
            True if acquired, False if rate limited
        """
        async with self._lock:
            bucket = self._get_bucket(key)

            # Check global limit first
            if self.global_bucket and not self.global_bucket.consume(tokens):
                log_event(
                    "rate_limit_global",
                    level="debug",
                    key=key,
                )
                return False

            # Check per-key limit
            if not bucket.consume(tokens):
                log_event(
                    "rate_limit_key",
                    level="debug",
                    key=key,
                )
                # Restore global tokens if per-key failed
                if self.global_bucket:
                    self.global_bucket.tokens = min(
                        self.global_bucket.capacity, self.global_bucket.tokens + tokens
                    )
                return False

            return True

    async def wait_for_token(
        self,
        key: str,
        tokens: float = 1,
        timeout: float = 30.0,
    ) -> bool:
        """
        Wait for tokens to become available (blocking).

        Args:
            key: Rate limit key
            tokens: Number of tokens to acquire
            timeout: Maximum seconds to wait

        Returns:
            True if tokens acquired, False if timeout
        """
        start = time.monotonic()

        while True:
            if await self.acquire(key, tokens):
                return True

            elapsed = time.monotonic() - start
            if elapsed >= timeout:
                log_event(
                    "rate_limit_timeout",
                    level="warning",
                    key=key,
                    timeout=timeout,
                )
                return False

            # Calculate wait time
            async with self._lock:
                bucket = self._get_bucket(key)
                wait = bucket.wait_time(tokens)

                # Also check global
                if self.global_bucket:
                    global_wait = self.global_bucket.wait_time(tokens)
                    wait = max(wait, global_wait)

            # Don't wait longer than remaining timeout
            remaining = timeout - elapsed
            wait = min(wait, remaining, 1.0)  # Cap at 1 second intervals

            if wait > 0:
                await asyncio.sleep(wait)

    def get_stats(self, key: str) -> Dict[str, float]:
        """Get current stats for a key."""
        if key not in self.buckets:
            return {
                "tokens": self.capacity,
                "capacity": self.capacity,
                "refill_rate": self.refill_rate,
            }

        bucket = self.buckets[key]
        bucket.refill()
        return {
            "tokens": bucket.tokens,
            "capacity": bucket.capacity,
            "refill_rate": bucket.refill_rate,
        }

    def reset(self, key: Optional[str] = None) -> None:
        """Reset bucket(s) to full capacity."""
        if key:
            if key in self.buckets:
                self.buckets[key].tokens = self.capacity
                self.buckets[key].last_refill = time.monotonic()
        else:
            self.buckets.clear()
            if self.global_bucket:
                self.global_bucket.tokens = self.global_bucket.capacity
                self.global_bucket.last_refill = time.monotonic()


# =============================================================================
# DEFAULT LIMITER INSTANCE
# =============================================================================

# Default WhatsApp rate limiter
# 80 msgs/sec per phone number, 500 msgs/sec global
default_limiter = TokenBucketRateLimiter(
    capacity=80,
    refill_rate=80,
    global_capacity=500,
    global_refill_rate=500,
)
