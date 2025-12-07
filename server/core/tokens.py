"""
Token Management Service for TREEEX-WBSP

Manages Meta WhatsApp access tokens:
- Retrieves long-term tokens from database
- Caches short-term tokens in Redis
- Handles token refresh and expiry
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.db import async_session_maker
from server.core.monitoring import log_event, log_exception
from server.core.redis import TTL, cache_get, cache_set, key_access_token
from server.models.contacts import PhoneNumber


async def get_access_token(phone_number_id: UUID) -> Optional[str]:
    """
    Get access token for a phone number.
    
    Returns cached short-term token if available, otherwise retrieves
    the long-term token from database.
    
    Args:
        phone_number_id: UUID of the phone number
        
    Returns:
        Access token string or None if not found
    """
    try:
        # Check cache first
        cached_token = await get_cached_token(phone_number_id)
        if cached_token:
            log_event(
                "token_cache_hit",
                level="debug",
                phone_number_id=str(phone_number_id),
            )
            return cached_token

        # Cache miss - get from database
        async with async_session_maker() as session:
            result = await session.execute(
                select(PhoneNumber).where(
                    PhoneNumber.id == phone_number_id,
                    PhoneNumber.deleted_at.is_(None),
                )
            )
            phone_number = result.scalar_one_or_none()

            if not phone_number:
                log_event(
                    "token_phone_not_found",
                    level="warning",
                    phone_number_id=str(phone_number_id),
                )
                return None

            token = phone_number.access_token

            # Cache the token for future use
            await cache_token(phone_number_id, token, TTL.ACCESS_TOKEN)

            log_event(
                "token_retrieved_from_db",
                level="debug",
                phone_number_id=str(phone_number_id),
            )

            return token

    except Exception as e:
        log_exception("get_access_token_failed", e, phone_number_id=str(phone_number_id))
        return None


async def refresh_access_token(phone_number_id: UUID) -> Optional[str]:
    """
    Force refresh the access token from database.
    
    Invalidates cache and retrieves fresh token from database.
    
    Args:
        phone_number_id: UUID of the phone number
        
    Returns:
        Fresh access token string or None if not found
    """
    try:
        async with async_session_maker() as session:
            result = await session.execute(
                select(PhoneNumber).where(
                    PhoneNumber.id == phone_number_id,
                    PhoneNumber.deleted_at.is_(None),
                )
            )
            phone_number = result.scalar_one_or_none()

            if not phone_number:
                log_event(
                    "token_refresh_phone_not_found",
                    level="warning",
                    phone_number_id=str(phone_number_id),
                )
                return None

            token = phone_number.access_token

            # Update cache with fresh token
            await cache_token(phone_number_id, token, TTL.ACCESS_TOKEN)

            log_event(
                "token_refreshed",
                level="info",
                phone_number_id=str(phone_number_id),
            )

            return token

    except Exception as e:
        log_exception("refresh_access_token_failed", e, phone_number_id=str(phone_number_id))
        return None


async def cache_token(phone_number_id: UUID, token: str, ttl: int) -> bool:
    """
    Cache access token in Redis.
    
    Args:
        phone_number_id: UUID of the phone number
        token: Access token to cache
        ttl: Time to live in seconds
        
    Returns:
        True if cached successfully, False otherwise
    """
    try:
        key = key_access_token(str(phone_number_id))
        success = await cache_set(key, token, ttl=ttl, serialize=False)
        
        if success:
            log_event(
                "token_cached",
                level="debug",
                phone_number_id=str(phone_number_id),
                ttl=ttl,
            )
        
        return success

    except Exception as e:
        log_exception("cache_token_failed", e, phone_number_id=str(phone_number_id))
        return False


async def get_cached_token(phone_number_id: UUID) -> Optional[str]:
    """
    Get cached access token from Redis.
    
    Args:
        phone_number_id: UUID of the phone number
        
    Returns:
        Cached token string or None if not found/expired
    """
    try:
        key = key_access_token(str(phone_number_id))
        token = await cache_get(key, deserialize=False)
        return token

    except Exception as e:
        log_exception("get_cached_token_failed", e, phone_number_id=str(phone_number_id))
        return None
