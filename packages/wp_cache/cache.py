"""
Cache module for the week planner application.
Provides a unified interface for caching with Redis fallback.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from packages.wp_cache.redis_safe import (
    get_sync_client,
    should_bypass_redis,
    get_redis_status,
)

logger = logging.getLogger(__name__)


class CacheClient:
    """
    Unified cache client with Redis backend and fallback support.

    Handles JSON serialization/deserialization and provides a clean interface
    for caching operations.
    """

    def __init__(self, default_ttl: int = 3600):
        """
        Initialize cache client.

        Args:
            default_ttl: Default TTL in seconds for cached items
        """
        self.default_ttl = default_ttl
        self._redis_client = None
        self._cache_bypass = should_bypass_redis()

        if not self._cache_bypass:
            try:
                self._redis_client = get_sync_client()
                logger.info("Cache client initialized with Redis")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis client: {e}")
                self._cache_bypass = True

    def get_json(self, key: str) -> Optional[Union[Dict, List]]:
        """
        Get JSON value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value (dict/list) or None if not found
        """
        if self._cache_bypass:
            logger.debug(f"Cache bypassed for key: {key}")
            return None

        if not self._redis_client:
            return None

        try:
            value = self._redis_client.get(key)
            if value is None:
                logger.debug(f"Cache miss for key: {key}")
                return None

            # Декодируем bytes в строку и парсим JSON
            if isinstance(value, bytes):
                value = value.decode("utf-8")

            parsed_value = json.loads(value)
            logger.debug(f"Cache hit for key: {key}")
            return parsed_value

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to decode JSON for key {key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    def set_json(
        self, key: str, value: Union[Dict, List], ttl: Optional[int] = None
    ) -> bool:
        """
        Set JSON value in cache.

        Args:
            key: Cache key
            value: Value to cache (dict or list)
            ttl: TTL in seconds (uses default if None)

        Returns:
            True if successful, False otherwise
        """
        if self._cache_bypass:
            logger.debug(f"Cache bypassed for key: {key}")
            return False

        if not self._redis_client:
            return False

        try:
            # Сериализуем в JSON строку
            json_value = json.dumps(value, ensure_ascii=False)

            # Устанавливаем TTL
            actual_ttl = ttl if ttl is not None else self.default_ttl

            # Сохраняем в Redis
            result = self._redis_client.setex(key, actual_ttl, json_value)

            if result:
                logger.debug(f"Cached value for key: {key} with TTL: {actual_ttl}s")
            else:
                logger.warning(f"Failed to cache value for key: {key}")

            return bool(result)

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    def with_fallback(
        self,
        key: str,
        producer: Callable[[], Union[Dict, List]],
        ttl: Optional[int] = None,
    ) -> Union[Dict, List]:
        """
        Get value from cache or produce it if not found.

        Args:
            key: Cache key
            producer: Function to produce value if not in cache
            ttl: TTL for cached value (uses default if None)

        Returns:
            Value from cache or produced value
        """
        # Пытаемся получить из кэша
        cached_value = self.get_json(key)
        if cached_value is not None:
            return cached_value

        # Кэш miss - производим значение
        logger.debug(f"Cache miss for key: {key}, producing value")
        try:
            value = producer()

            # Кэшируем результат
            self.set_json(key, value, ttl)

            return value

        except Exception as e:
            logger.error(f"Producer failed for key {key}: {e}")
            # Возвращаем пустое значение в случае ошибки
            if isinstance(producer(), dict):
                return {}
            else:
                return []

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if successful, False otherwise
        """
        if self._cache_bypass or not self._redis_client:
            return False

        try:
            result = self._redis_client.delete(key)
            if result:
                logger.debug(f"Deleted cache key: {key}")
            return bool(result)
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists, False otherwise
        """
        if self._cache_bypass or not self._redis_client:
            return False

        try:
            return bool(self._redis_client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False

    def get_ttl(self, key: str) -> Optional[int]:
        """
        Get remaining TTL for key.

        Args:
            key: Cache key

        Returns:
            Remaining TTL in seconds or None if key doesn't exist
        """
        if self._cache_bypass or not self._redis_client:
            return None

        try:
            ttl = self._redis_client.ttl(key)
            return ttl if ttl > 0 else None
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return None

    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern.

        Args:
            pattern: Redis pattern (e.g., "v2:bangkok:*")

        Returns:
            Number of keys deleted
        """
        if self._cache_bypass or not self._redis_client:
            return 0

        try:
            keys = self._redis_client.keys(pattern)
            if keys:
                deleted = self._redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} keys matching pattern: {pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        stats = {
            "cache_enabled": not self._cache_bypass,
            "redis_status": get_redis_status(),
            "default_ttl": self.default_ttl,
            "timestamp": datetime.now().isoformat(),
        }

        if not self._cache_bypass and self._redis_client:
            try:
                # Получаем информацию о Redis
                info = self._redis_client.info()
                stats.update(
                    {
                        "redis_version": info.get("redis_version"),
                        "connected_clients": info.get("connected_clients"),
                        "used_memory_human": info.get("used_memory_human"),
                        "total_commands_processed": info.get(
                            "total_commands_processed"
                        ),
                    }
                )
            except Exception as e:
                stats["redis_info_error"] = str(e)

        return stats


def get_cache_client(default_ttl: int = 3600) -> CacheClient:
    """
    Get a cache client instance.

    Args:
        default_ttl: Default TTL in seconds

    Returns:
        CacheClient instance
    """
    return CacheClient(default_ttl)
