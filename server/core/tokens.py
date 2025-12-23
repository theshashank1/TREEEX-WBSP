"""
Token Management Service - server/core/tokens.py

Manages Meta WhatsApp access tokens:
- Retrieves long-term tokens from database
- Caches short-term tokens in Redis
- Handles token refresh
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select

from server.core.db import async_session_maker
from server.core.monitoring import log_event, log_exception
from server.core.redis import TTL, cache_get, cache_set, key_access_token
from server.models.contacts import Channel


async def get_access_token(channel_id: UUID) -> Optional[str]:
    """
    Get access token for a channel.

    Returns cached short-term token if available, otherwise retrieves from database.
    """
    try:
        # Check cache first
        cached_token = await get_cached_token(channel_id)
        if cached_token:
            log_event(
                "token_cache_hit",
                level="debug",
                channel_id=str(channel_id),
            )
            return cached_token

        # Cache miss - get from database
        async with async_session_maker() as session:
            result = await session.execute(
                select(Channel).where(
                    Channel.id == channel_id,
                    Channel.deleted_at.is_(None),
                )
            )
            channel = result.scalar_one_or_none()

            if not channel:
                log_event(
                    "token_channel_not_found",
                    level="warning",
                    channel_id=str(channel_id),
                )
                return None

            token = channel.access_token

            if not token or token.strip() == "":
                log_event(
                    "token_empty_in_db",
                    level="warning",
                    channel_id=str(channel_id),
                )
                return None

            # Cache the token for future use
            await cache_token(channel_id, token, TTL.ACCESS_TOKEN)

            log_event(
                "token_retrieved_from_db",
                level="debug",
                channel_id=str(channel_id),
            )

            return token

    except Exception as e:
        log_exception(
            "get_access_token_failed", e, channel_id=str(channel_id)
        )
        return None


async def refresh_access_token(channel_id: UUID) -> Optional[str]:
    """
    Force refresh the access token from database.

    Invalidates cache and retrieves fresh token from database.
    """
    try:
        async with async_session_maker() as session:
            result = await session.execute(
                select(Channel).where(
                    Channel.id == channel_id,
                    Channel.deleted_at.is_(None),
                )
            )
            channel = result.scalar_one_or_none()

            if not channel:
                log_event(
                    "token_refresh_channel_not_found",
                    level="warning",
                    channel_id=str(channel_id),
                )
                return None

            token = channel.access_token

            if not token or token.strip() == "":
                log_event(
                    "token_refresh_empty_in_db",
                    level="warning",
                    channel_id=str(channel_id),
                )
                return None

            # Update cache with fresh token
            await cache_token(channel_id, token, TTL.ACCESS_TOKEN)

            log_event(
                "token_refreshed",
                level="info",
                channel_id=str(channel_id),
            )

            return token

    except Exception as e:
        log_exception(
            "refresh_access_token_failed", e, channel_id=str(channel_id)
        )
        return None


async def cache_token(channel_id: UUID, token: str, ttl: int) -> bool:
    """Cache access token in Redis."""
    try:
        key = key_access_token(str(channel_id))
        success = await cache_set(key, token, ttl=ttl, serialize=False)

        if success:
            log_event(
                "token_cached",
                level="debug",
                channel_id=str(channel_id),
                ttl=ttl,
            )

        return success

    except Exception as e:
        log_exception("cache_token_failed", e, channel_id=str(channel_id))
        return False


async def get_cached_token(channel_id: UUID) -> Optional[str]:
    """Get cached access token from Redis."""
    try:
        key = key_access_token(str(channel_id))
        token = await cache_get(key, deserialize=False)
        return token

    except Exception as e:
        log_exception(
            "get_cached_token_failed", e, channel_id=str(channel_id)
        )
        return None
