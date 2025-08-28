#!/usr/bin/env python
"""
Redis cache operations for places - thin wrapper around core/cache.py.
"""

import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import redis

from .models_places.place import Place
from .logging import logger

# Import the unified cache implementation
from .cache import ensure_client, is_configured


def get_redis_client():
    """
    Get Redis client from unified cache implementation.

    Returns:
        Redis client instance
    """
    if not is_configured():
        return None
    return ensure_client()


def get_place_cache_key(city: str, flag: str) -> str:
    """Generate Redis cache key for places (v1 format)."""
    return f"v1:places:{city}:flag:{flag}"


def get_place_index_key(city: str) -> str:
    """Generate Redis cache key for place index (v1 format)."""
    return f"v1:places:{city}:index"


def get_place_stale_key(city: str, flag: str) -> str:
    """Generate Redis stale cache key for places (v1 format)."""
    return f"v1:places:{city}:flag:{flag}:stale"


def cache_places(city: str, flag: str, places: List[Place], ttl: int = 3600) -> bool:
    """
    Cache places in Redis using unified cache implementation.

    Args:
        city: City name
        flag: Flag name
        places: List of places to cache
        ttl: Time to live in seconds

    Returns:
        True if successful
    """
    client = get_redis_client()
    if not client:
        return False

    try:
        cache_key = get_place_cache_key(city, flag)

        # Конвертируем места в JSON
        places_data = []
        for place in places:
            place_dict = place.to_dict()
            # Убираем поля, которые не нужны в кэше
            place_dict.pop("created_at", None)
            place_dict.pop("updated_at", None)
            places_data.append(place_dict)

        # Кэшируем места
        client.setex(cache_key, ttl, json.dumps(places_data))

        # Обновляем индекс
        index_key = get_place_index_key(city)
        client.sadd(index_key, flag)
        client.expire(index_key, ttl + 3600)  # Индекс живет дольше

        logger.debug(f"Cached {len(places)} places for {city}:{flag}")
        return True

    except Exception as e:
        logger.error(f"Error caching places for {city}:{flag}: {e}")
        return False


def get_cached_places(city: str, flag: str) -> Optional[List[Place]]:
    """
    Get places from cache using unified cache implementation.

    Args:
        city: City name
        flag: Flag name

    Returns:
        List of Place objects or None if not cached
    """
    client = get_redis_client()
    if not client:
        return None

    try:
        cache_key = get_place_cache_key(city, flag)
        cached_data = client.get(cache_key)

        if not cached_data:
            return None

        # Парсим JSON и создаем Place объекты
        places_data = json.loads(cached_data)
        places = []

        for place_dict in places_data:
            try:
                place = Place.from_dict(place_dict)
                places.append(place)
            except Exception as e:
                logger.warning(f"Error creating Place from cached data: {e}")
                continue

        logger.debug(f"Retrieved {len(places)} places from cache for {city}:{flag}")
        return places

    except Exception as e:
        logger.error(f"Error getting places from cache for {city}:{flag}: {e}")
        return None


def cache_places_stale(
    city: str, flag: str, places: List[Place], ttl: int = 86400
) -> bool:
    """
    Cache places in stale cache (longer TTL) using unified cache implementation.

    Args:
        city: City name
        flag: Flag name
        places: List of places to cache
        ttl: Time to live in seconds (default: 24 hours)

    Returns:
        True if successful
    """
    client = get_redis_client()
    if not client:
        return False

    try:
        stale_key = get_place_stale_key(city, flag)

        # Конвертируем места в JSON
        places_data = []
        for place in places:
            place_dict = place.to_dict()
            # Убираем поля, которые не нужны в кэше
            place_dict.pop("created_at", None)
            place_dict.pop("updated_at", None)
            places_data.append(place_dict)

        # Кэшируем места в stale кэше
        client.setex(stale_key, ttl, json.dumps(places_data))

        logger.debug(f"Cached {len(places)} places in stale cache for {city}:{flag}")
        return True

    except Exception as e:
        logger.error(f"Error caching places in stale cache for {city}:{flag}: {e}")
        return False


def get_cached_places_stale(city: str, flag: str) -> Optional[List[Place]]:
    """
    Get places from stale cache using unified cache implementation.

    Args:
        city: City name
        flag: Flag name

    Returns:
        List of Place objects or None if not cached
    """
    client = get_redis_client()
    if not client:
        return None

    try:
        stale_key = get_place_stale_key(city, flag)
        cached_data = client.get(stale_key)

        if not cached_data:
            return None

        # Парсим JSON и создаем Place объекты
        places_data = json.loads(cached_data)
        places = []

        for place_dict in places_data:
            try:
                place = Place.from_dict(place_dict)
                places.append(place)
            except Exception as e:
                logger.warning(f"Error creating Place from stale cache data: {e}")
                continue

        logger.debug(
            f"Retrieved {len(places)} places from stale cache for {city}:{flag}"
        )
        return places

    except Exception as e:
        logger.error(f"Error getting places from stale cache for {city}:{flag}: {e}")
        return None


def get_cached_places_with_fallback(city: str, flag: str) -> Optional[List[Place]]:
    """
    Get places from cache with fallback to stale cache using unified cache implementation.

    Args:
        city: City name
        flag: Flag name

    Returns:
        List of Place objects or None if not cached anywhere
    """
    # Сначала пробуем основной кэш
    places = get_cached_places(city, flag)
    if places:
        return places

    # Если нет в основном кэше, пробуем stale кэш
    places = get_cached_places_stale(city, flag)
    if places:
        logger.info(f"Using stale cache for {city}:{flag}")
        return places

    return None


def invalidate_places_cache(city: str, flag: Optional[str] = None) -> bool:
    """
    Invalidate places cache using unified cache implementation.

    Args:
        city: City name
        flag: Flag name (if None, invalidate all flags for city)

    Returns:
        True if successful
    """
    client = get_redis_client()
    if not client:
        return False

    try:
        if flag:
            # Инвалидируем конкретный флаг
            cache_key = get_place_cache_key(city, flag)
            stale_key = get_place_stale_key(city, flag)
            client.delete(cache_key, stale_key)
            logger.debug(f"Invalidated cache for {city}:{flag}")
        else:
            # Инвалидируем все флаги для города
            index_key = get_place_index_key(city)
            cached_flags = client.smembers(index_key)

            for cached_flag in cached_flags:
                cache_key = get_place_cache_key(city, cached_flag)
                stale_key = get_place_stale_key(city, cached_flag)
                client.delete(cache_key, stale_key)

            # Удаляем индекс
            client.delete(index_key)
            logger.debug(f"Invalidated all cache for {city}")

        return True

    except Exception as e:
        logger.error(f"Error invalidating places cache for {city}:{flag}: {e}")
        return False


def get_cache_stats(city: str) -> Dict[str, Any]:
    """
    Get cache statistics for a city using unified cache implementation.

    Args:
        city: City name

    Returns:
        Dictionary with cache statistics
    """
    client = get_redis_client()
    if not client:
        return {"error": "Redis not available"}

    try:
        index_key = get_place_index_key(city)
        cached_flags = client.smembers(index_key)

        stats = {"city": city, "cached_flags": list(cached_flags), "flag_details": {}}

        for flag in cached_flags:
            cache_key = get_place_cache_key(city, flag)
            stale_key = get_place_stale_key(city, flag)

            # Проверяем TTL для каждого кэша
            cache_ttl = client.ttl(cache_key)
            stale_ttl = client.ttl(stale_key)

            # Проверяем размер кэша
            cache_size = client.memory_usage(cache_key) or 0
            stale_size = client.memory_usage(stale_key) or 0

            stats["flag_details"][flag] = {
                "cache_ttl": cache_ttl,
                "stale_ttl": stale_ttl,
                "cache_size_bytes": cache_size,
                "stale_size_bytes": stale_size,
            }

        return stats

    except Exception as e:
        logger.error(f"Error getting cache stats for {city}: {e}")
        return {"city": city, "error": str(e)}


def warm_places_cache(
    city: str, flags: List[str], fetcher, ttl: int = 3600
) -> Dict[str, int]:
    """
    Warm up places cache for specified flags using unified cache implementation.

    Args:
        city: City name
        flags: List of flags to warm up
        fetcher: Places fetcher instance
        ttl: Cache TTL in seconds

    Returns:
        Dictionary with results for each flag
    """
    results = {}

    for flag in flags:
        try:
            logger.info(f"Warming up cache for {city}:{flag}")

            # Получаем места для флага
            places = fetcher.fetch(city, category=flag, limit=100)

            if places:
                # Кэшируем места
                success = cache_places(city, flag, places, ttl)
                if success:
                    results[flag] = len(places)
                    logger.info(
                        f"Successfully cached {len(places)} places for {city}:{flag}"
                    )
                else:
                    results[flag] = 0
                    logger.warning(f"Failed to cache places for {city}:{flag}")
            else:
                results[flag] = 0
                logger.warning(f"No places found for {city}:{flag}")

        except Exception as e:
            logger.error(f"Error warming up cache for {city}:{flag}: {e}")
            results[flag] = 0

    return results


def healthcheck() -> bool:
    """
    Simple Redis health check using unified cache implementation.

    Returns:
        True if Redis is accessible
    """
    try:
        client = get_redis_client()
        if not client:
            return False

        # Простая проверка
        client.ping()
        return True

    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False
