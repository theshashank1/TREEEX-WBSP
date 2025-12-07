"""
Redis Client & Queue Management for TREEEX-WBSP
Handles connection pooling, caching, queue operations, and pub/sub
"""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from enum import Enum
from typing import Any, Callable, Optional, TypeVar

import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import RedisError

from server.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ============================================================================
# QUEUE NAMES
# ============================================================================


class Queue(str, Enum):
    """Queue names for async job processing"""

    # Core messaging
    OUTBOUND_MESSAGES = "queue:outbound"
    INBOUND_WEBHOOKS = "queue:webhooks"
    MESSAGE_STATUS = "queue:status"

    # Media (Azure Blob)
    MEDIA_DOWNLOAD = "queue:media:download"
    MEDIA_UPLOAD = "queue:media:upload"

    # Campaigns
    CAMPAIGN_JOBS = "queue:campaigns"

    # Templates
    TEMPLATE_SYNC = "queue:templates"

    # Priority & DLQ
    HIGH_PRIORITY = "queue:priority"
    DEAD_LETTER = "queue:dlq"


# ============================================================================
# TTL CONSTANTS (seconds)
# ============================================================================


class TTL:
    """Cache TTL values in seconds"""

    IDEMPOTENCY = 86400  # 24 hours - webhook deduplication
    SESSION = 604800  # 7 days - user sessions
    CACHE = 3600  # 1 hour - general cache
    RATE_LIMIT = 60  # 1 minute - rate limit windows
    VERIFICATION = 300  # 5 minutes - codes
    CONVERSATION_WINDOW = 86400  # 24 hours - WhatsApp session window
    ACCESS_TOKEN = 3600  # 1 hour - Meta short-lived tokens
    ACCESS_TOKEN_BUFFER = 300  # 5 min buffer before expiry


# ============================================================================
# CACHE KEY BUILDERS
# ============================================================================


def key_idempotency(workspace_id: str, event_hash: str) -> str:
    """Webhook idempotency key"""
    return f"idempotency:{workspace_id}:{event_hash}"


def key_rate_limit(phone_number_id: str) -> str:
    """Outbound rate limit key"""
    return f"ratelimit:{phone_number_id}"


def key_api_rate_limit(workspace_id: str, endpoint: str) -> str:
    """API rate limit key"""
    return f"ratelimit:api:{workspace_id}:{endpoint}"


def key_session(user_id: str) -> str:
    """User session key"""
    return f"session:{user_id}"


def key_conversation_window(conversation_id: str) -> str:
    """24h conversation window tracking"""
    return f"window:{conversation_id}"


def key_realtime(workspace_id: str, event_type: str = "messages") -> str:
    """Pub/sub channel for real-time events"""
    return f"realtime:{workspace_id}:{event_type}"


def key_access_token(phone_number_id: str) -> str:
    """Short-term access token cache key"""
    return f"token:access:{phone_number_id}"


# ============================================================================
# REDIS CLIENT
# ============================================================================

_redis: Optional[Redis] = None


async def get_redis() -> Redis:
    """
    Get Redis client.  Initializes connection on first call.

    Usage:
        redis = await get_redis()
        await redis.set("key", "value")
    """
    global _redis

    if _redis is None:
        if not settings.REDIS_URL:
            raise RuntimeError("REDIS_URL not configured in settings")

        _redis = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
        )

        # Verify connection
        await _redis.ping()
        logger.info("✅ Redis connected")

    return _redis


async def close_redis() -> None:
    """Close Redis connection.  Call on app shutdown."""
    global _redis

    if _redis is not None:
        await _redis.close()
        _redis = None
        logger.info("✅ Redis closed")


async def redis_health() -> bool:
    """Check Redis connection health"""
    try:
        r = await get_redis()
        await r.ping()
        return True
    except RedisError as e:
        logger.error(f"Redis health check failed: {e}")
        return False


# ============================================================================
# CORE OPERATIONS
# ============================================================================


async def cache_get(key: str, deserialize: bool = True) -> Optional[Any]:
    """Get value from cache"""
    try:
        r = await get_redis()
        value = await r.get(key)
        if value and deserialize:
            return json.loads(value)
        return value
    except RedisError as e:
        logger.error(f"cache_get failed [{key}]: {e}")
        return None


async def cache_set(
    key: str, value: Any, ttl: int = TTL.CACHE, serialize: bool = True
) -> bool:
    """Set value in cache with TTL"""
    try:
        r = await get_redis()
        if serialize:
            value = json.dumps(value)
        await r.setex(key, ttl, value)
        return True
    except RedisError as e:
        logger.error(f"cache_set failed [{key}]: {e}")
        return False


async def cache_delete(key: str) -> bool:
    """Delete key from cache"""
    try:
        r = await get_redis()
        await r.delete(key)
        return True
    except RedisError as e:
        logger.error(f"cache_delete failed [{key}]: {e}")
        return False


# ============================================================================
# IDEMPOTENCY
# ============================================================================


async def is_duplicate(key: str, ttl: int = TTL.IDEMPOTENCY) -> bool:
    """
    Check if operation already processed (idempotency).
    Uses SET NX - returns True if duplicate, False if new.

    Usage:
        if await is_duplicate(key_idempotency(workspace_id, event_hash)):
            return  # Skip duplicate
        # Process new event...
    """
    try:
        r = await get_redis()
        result = await r.set(key, "1", ex=ttl, nx=True)
        return result is None  # None = key existed = duplicate
    except RedisError as e:
        logger.error(f"is_duplicate check failed [{key}]: {e}")
        return False  # Allow on error (fail open)


# ============================================================================
# RATE LIMITING
# ============================================================================


async def check_rate_limit(key: str, limit: int, window: int = 60) -> tuple[bool, int]:
    """
    Fixed window rate limiting.

    Returns:
        (allowed: bool, remaining: int)

    Usage:
        allowed, remaining = await check_rate_limit(
            key_rate_limit(phone_number_id),
            limit=settings.RATE_LIMIT_MESSAGES_PER_SECOND * 60,
            window=60
        )
        if not allowed:
            raise HTTPException(429, "Rate limit exceeded")
    """
    try:
        r = await get_redis()
        current = await r.incr(key)

        if current == 1:
            await r.expire(key, window)

        allowed = current <= limit
        remaining = max(0, limit - current)
        return allowed, remaining
    except RedisError as e:
        logger.error(f"rate_limit check failed [{key}]: {e}")
        return True, limit  # Fail open


# ============================================================================
# QUEUE OPERATIONS
# ============================================================================


async def enqueue(queue: Queue, data: dict, priority: bool = False) -> bool:
    """
    Add job to queue.

    Args:
        queue: Queue enum value
        data: Job payload (will be JSON serialized)
        priority: If True, adds to front of queue
    """
    try:
        r = await get_redis()
        payload = json.dumps(data)

        if priority:
            await r.rpush(queue.value, payload)  # Front
        else:
            await r.lpush(queue.value, payload)  # Back

        return True
    except RedisError as e:
        logger.error(f"enqueue failed [{queue.value}]: {e}")
        return False


async def dequeue(queue: Queue, timeout: int = 5) -> Optional[dict]:
    """
    Get job from queue (blocking).

    Args:
        queue: Queue enum value
        timeout: Seconds to wait if queue empty

    Returns:
        Job data dict or None if timeout
    """
    try:
        r = await get_redis()
        result = await r.brpop(queue.value, timeout=timeout)

        if result:
            _, payload = result
            return json.loads(payload)
        return None
    except RedisError as e:
        logger.error(f"dequeue failed [{queue.value}]: {e}")
        return None


async def queue_length(queue: Queue) -> int:
    """Get number of jobs in queue"""
    try:
        r = await get_redis()
        return await r.llen(queue.value)
    except RedisError as e:
        logger.error(f"queue_length failed [{queue. value}]: {e}")
        return 0


async def move_to_dlq(queue: Queue, data: dict, error: str) -> bool:
    """Move failed job to dead letter queue with error info"""
    dlq_data = {
        "original_queue": queue.value,
        "data": data,
        "error": error,
    }
    return await enqueue(Queue.DEAD_LETTER, dlq_data)


# ============================================================================
# PUB/SUB (Real-time Events)
# ============================================================================


async def publish(channel: str, data: dict) -> bool:
    """
    Publish message to channel (for Socket.IO/WebSocket relay).

    Usage:
        await publish(
            key_realtime(workspace_id, "messages"),
            {"type": "new_message", "data": message_dict}
        )
    """
    try:
        r = await get_redis()
        await r.publish(channel, json.dumps(data))
        return True
    except RedisError as e:
        logger.error(f"publish failed [{channel}]: {e}")
        return False


@asynccontextmanager
async def subscribe(channel: str):
    """
    Subscribe to channel.  Use as async context manager.

    Usage:
        async with subscribe(key_realtime(workspace_id)) as messages:
            async for msg in messages:
                print(msg)
    """
    r = await get_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe(channel)

    async def message_generator():
        async for message in pubsub.listen():
            if message["type"] == "message":
                yield json.loads(message["data"])

    try:
        yield message_generator()
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()


# ============================================================================
# FASTAPI INTEGRATION
# ============================================================================


async def startup() -> None:
    """Call from FastAPI lifespan startup"""
    await get_redis()


async def shutdown() -> None:
    """Call from FastAPI lifespan shutdown"""
    await close_redis()
