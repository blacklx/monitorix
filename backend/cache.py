"""
Copyright 2024 Monitorix Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import json
import logging
from typing import Optional, Any, Callable
from functools import wraps
from datetime import timedelta
import redis
from config import settings

logger = logging.getLogger(__name__)

# Redis client (None if Redis is disabled)
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """Get or create Redis client."""
    global _redis_client
    
    if not settings.redis_enabled:
        return None
    
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            _redis_client.ping()
            logger.info("Redis connection established")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            _redis_client = None
        except Exception as e:
            logger.error(f"Redis initialization error: {e}. Caching disabled.")
            _redis_client = None
    
    return _redis_client


def get_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a cache key from prefix and arguments."""
    key_parts = [prefix]
    
    # Add positional arguments
    for arg in args:
        if arg is not None:
            key_parts.append(str(arg))
    
    # Add keyword arguments (sorted for consistency)
    for key, value in sorted(kwargs.items()):
        if value is not None:
            key_parts.append(f"{key}:{value}")
    
    return ":".join(key_parts)


def get(key: str) -> Optional[Any]:
    """Get value from cache."""
    client = get_redis_client()
    if not client:
        return None
    
    try:
        value = client.get(key)
        if value:
            return json.loads(value)
    except (redis.RedisError, json.JSONDecodeError) as e:
        logger.warning(f"Cache get error for key {key}: {e}")
    
    return None


def set(key: str, value: Any, ttl: int = 300) -> bool:
    """Set value in cache with TTL (default 5 minutes)."""
    client = get_redis_client()
    if not client:
        return False
    
    try:
        client.setex(key, ttl, json.dumps(value, default=str))
        return True
    except (redis.RedisError, TypeError) as e:
        logger.warning(f"Cache set error for key {key}: {e}")
        return False


def delete(key: str) -> bool:
    """Delete key from cache."""
    client = get_redis_client()
    if not client:
        return False
    
    try:
        client.delete(key)
        return True
    except redis.RedisError as e:
        logger.warning(f"Cache delete error for key {key}: {e}")
        return False


def delete_pattern(pattern: str) -> int:
    """Delete all keys matching pattern."""
    client = get_redis_client()
    if not client:
        return 0
    
    try:
        keys = client.keys(pattern)
        if keys:
            return client.delete(*keys)
        return 0
    except redis.RedisError as e:
        logger.warning(f"Cache delete pattern error for {pattern}: {e}")
        return 0


def invalidate_cache(prefix: str) -> int:
    """Invalidate all cache keys with given prefix."""
    pattern = f"{prefix}:*"
    return delete_pattern(pattern)


def cached(prefix: str, ttl: int = 300):
    """
    Decorator to cache function results.
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds (default 5 minutes)
    
    Usage:
        @cached("dashboard:stats", ttl=60)
        def get_stats():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function arguments
            cache_key = get_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value
            
            # Cache miss - execute function
            logger.debug(f"Cache miss: {cache_key}")
            result = await func(*args, **kwargs) if hasattr(func, '__code__') and 'async' in str(func.__code__.co_flags) else func(*args, **kwargs)
            
            # Store in cache
            set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def clear_all_cache() -> bool:
    """Clear all cache (use with caution)."""
    client = get_redis_client()
    if not client:
        return False
    
    try:
        client.flushdb()
        logger.info("All cache cleared")
        return True
    except redis.RedisError as e:
        logger.error(f"Error clearing cache: {e}")
        return False

