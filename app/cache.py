"""Cache layer with Redis and memory fallback."""

import json
import logging
import time
from datetime import datetime
from typing import Any

import redis.asyncio as redis

from .config import settings

logger = logging.getLogger(__name__)

# Global Redis client (singleton)
_redis_client: redis.Redis | None = None

# In-memory cache as fallback
_memory_cache: dict[str, tuple[dict, float]] = {}


async def get_redis() -> redis.Redis | None:
    """Return Redis client (singleton pattern).

    Returns:
        Redis client or None if connection fails
    """
    global _redis_client

    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test connection
            await _redis_client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.warning(f"Redis not available: {e}. Using memory cache.")
            _redis_client = None

    return _redis_client


async def get_cached(key: str) -> dict | None:
    """Get value from cache (Redis or memory).

    Args:
        key: Cache key

    Returns:
        Deserialized value or None if not found
    """
    # Try Redis first
    try:
        client = await get_redis()
        if client:
            value = await client.get(key)
            if value:
                logger.debug(f"Cache HIT (Redis): {key}")
                cached = json.loads(value)
                return {k: v for k, v in cached.items() if k != "_cached_at"}
    except Exception as e:
        logger.warning(f"Error reading from Redis: {e}")

    # Fallback: memory
    if key in _memory_cache:
        value, expires_at = _memory_cache[key]
        if time.time() < expires_at:
            logger.debug(f"Cache HIT (memory): {key}")
            return {k: v for k, v in value.items() if k != "_cached_at"}
        else:
            # Expired
            del _memory_cache[key]
            logger.debug(f"Cache expired (memory): {key}")

    logger.debug(f"Cache MISS: {key}")
    return None


async def set_cached(
    key: str,
    value: dict,
    ttl: int | None = None,
) -> bool:
    """Save value to cache (Redis and memory).

    Args:
        key: Cache key
        value: Value to cache (dict)
        ttl: Time to live in seconds (default: settings.cache_ttl_insight)

    Returns:
        True if saved successfully
    """
    ttl = ttl or settings.cache_ttl_insight

    # Add cache timestamp without mutating caller's dict
    cache_value = dict(value)
    cache_value["_cached_at"] = datetime.utcnow().isoformat()

    # Serialize to JSON
    json_value = json.dumps(cache_value, default=str)

    # Save to Redis
    try:
        client = await get_redis()
        if client:
            await client.setex(key, ttl, json_value)
            logger.debug(f"Cache SET (Redis): {key} TTL={ttl}s")
    except Exception as e:
        logger.warning(f"Error saving to Redis: {e}")

    # Always save to memory as well (backup)
    _memory_cache[key] = (cache_value, time.time() + ttl)
    logger.debug(f"Cache SET (memory): {key} TTL={ttl}s")

    return True


async def delete_cached(key: str) -> bool:
    """Remove value from cache.

    Args:
        key: Key to remove

    Returns:
        True if removed
    """
    # Remove from Redis
    try:
        client = await get_redis()
        if client:
            await client.delete(key)
    except Exception as e:
        logger.warning(f"Error deleting from Redis: {e}")

    # Remove from memory
    if key in _memory_cache:
        del _memory_cache[key]

    return True


async def clear_forex_cache() -> int:
    """Clear all forex:* keys from cache.

    Returns:
        Number of keys removed
    """
    count = 0

    # Clear from Redis
    try:
        client = await get_redis()
        if client:
            keys = await client.keys("forex:*")
            if keys:
                count = await client.delete(*keys)
    except Exception as e:
        logger.warning(f"Error clearing Redis: {e}")

    # Clear from memory
    memory_keys = [k for k in _memory_cache if k.startswith("forex:")]
    for k in memory_keys:
        del _memory_cache[k]
        count += 1

    return count


async def get_cache_status() -> dict[str, Any]:
    """Return cache status for health check.

    Returns:
        Dict with status information
    """
    redis_status = "disconnected"
    redis_keys = 0

    try:
        client = await get_redis()
        if client:
            await client.ping()
            redis_status = "connected"
            keys = await client.keys("forex:*")
            redis_keys = len(keys) if keys else 0
    except Exception:
        pass

    return {
        "redis": redis_status,
        "redis_keys": redis_keys,
        "memory_keys": len(_memory_cache),
    }


async def list_sessions() -> list[dict[str, Any]]:
    """List all chat sessions from cache.

    Returns:
        List of session summaries with id, type, messages count, last activity
    """
    sessions = []

    # Patterns for session keys
    patterns = [
        ("chat:session:*", "chat"),
        ("docs_chat:session:*", "docs"),
    ]

    # Try Redis first
    try:
        client = await get_redis()
        if client:
            for pattern, session_type in patterns:
                keys = await client.keys(pattern)
                for key in keys or []:
                    try:
                        value = await client.get(key)
                        if value:
                            data = json.loads(value)
                            session_id = key.split(":")[-1]
                            sessions.append({
                                "session_id": session_id,
                                "type": session_type,
                                "messages_count": len(data.get("messages", [])),
                                "last_activity": data.get("last_activity"),
                                "created_at": data.get("created_at"),
                            })
                    except Exception as e:
                        logger.warning(f"Error reading session {key}: {e}")
    except Exception as e:
        logger.warning(f"Error listing sessions from Redis: {e}")

    # Also check memory cache
    for key, (value, _) in _memory_cache.items():
        if key.startswith("chat:session:") or key.startswith("docs_chat:session:"):
            session_id = key.split(":")[-1]
            # Skip if already in list from Redis
            if any(s["session_id"] == session_id for s in sessions):
                continue
            session_type = "chat" if key.startswith("chat:") else "docs"
            sessions.append({
                "session_id": session_id,
                "type": session_type,
                "messages_count": len(value.get("messages", [])),
                "last_activity": value.get("last_activity"),
                "created_at": value.get("created_at"),
            })

    # Sort by last_activity descending
    sessions.sort(key=lambda x: x.get("last_activity") or "", reverse=True)

    return sessions


async def delete_session(session_id: str) -> dict[str, Any]:
    """Delete a chat session from cache.

    Args:
        session_id: UUID of the session to delete

    Returns:
        Dict with deletion status and details
    """
    # Try both session types
    prefixes = ["chat:session:", "docs_chat:session:"]
    deleted = False
    session_type = None

    for prefix in prefixes:
        key = f"{prefix}{session_id}"

        # Check if exists before deleting
        exists = await get_cached(key) is not None

        if exists:
            await delete_cached(key)
            deleted = True
            session_type = "chat" if prefix.startswith("chat:") else "docs"
            logger.info(f"Deleted session {session_id} (type: {session_type})")
            break

    return {
        "deleted": deleted,
        "session_id": session_id,
        "type": session_type,
    }
