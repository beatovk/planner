#!/usr/bin/env python
"""
Places service that combines fetchers, database, and cache.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from packages.wp_places.fetchers.universal_places import UniversalPlacesFetcher
from packages.wp_places.dao import (
    init_schema, save_places, get_places_by_flags, 
    get_all_places, get_places_stats, load_from_json
)
from packages.wp_core.db import get_engine
from packages.wp_cache.redis_safe import get_sync_client, should_bypass_redis, get_redis_status
from packages.wp_models.place import Place
from packages.wp_tags.mapper import categories_to_place_flags
import logging
logger = logging.getLogger("places")


class PlacesService:
    """Service for managing places data."""
    
    def __init__(self):
        self.fetcher = UniversalPlacesFetcher()
        self._ensure_db_initialized()
    
    def _ensure_db_initialized(self):
        """Ensure places database is initialized."""
        try:
            engine = get_engine()
            init_schema(engine)
            logger.info("Places database schema initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize places database: {e}")
    
    def _get_redis_client(self):
        """Get Redis client from safe Redis implementation."""
        bypass = should_bypass_redis()
        logger.info(f"Redis bypass check: {bypass}")
        if bypass:
            return None
        client = get_sync_client()
        logger.info(f"Redis client created: {client is not None}")
        return client
    
    def _get_place_cache_key(self, city: str, flag: str) -> str:
        """Generate Redis cache key for places (v1 format)."""
        return f"v1:places:{city}:flag:{flag}"
    
    def _get_place_stale_key(self, city: str, flag: str) -> str:
        """Generate Redis cache key for place stale cache (v1 format)."""
        return f"v1:places:{city}:flag:{flag}:stale"
    
    def _get_place_index_key(self, city: str) -> str:
        """Generate Redis cache key for place index (v1 format)."""
        return f"v1:places:{city}:index"
    
    def _cache_places(self, city: str, flag: str, places: List[Place], ttl: int = 3600) -> bool:
        """Cache places using safe Redis implementation."""
        client = self._get_redis_client()
        if not client:
            logger.debug(f"Redis not available, skipping cache for {city}:{flag}")
            return False
        
        try:
            import json
            cache_key = self._get_place_cache_key(city, flag)
            
            # Convert places to JSON
            places_data = []
            for place in places:
                place_dict = place.to_dict()
                # Remove fields not needed in cache
                place_dict.pop("created_at", None)
                place_dict.pop("updated_at", None)
                places_data.append(place_dict)
            
            # Cache places with safe Redis operations
            try:
                # Set timeout for Redis operations
                client.setex(cache_key, ttl, json.dumps(places_data))
                
                # Update index
                index_key = self._get_place_index_key(city)
                client.sadd(index_key, flag)
                client.expire(index_key, ttl + 3600)  # Index lives longer
                
                logger.debug(f"Cached {len(places)} places for {city}:{flag}")
                return True
            except Exception as redis_error:
                logger.error(f"Redis operation failed for {city}:{flag}: {redis_error}")
                return False
            
        except Exception as e:
            logger.error(f"Error caching places for {city}:{flag}: {e}")
            return False
    
    def _get_cached_places(self, city: str, flag: str) -> Optional[List[Place]]:
        """Get places from cache using safe Redis implementation."""
        client = self._get_redis_client()
        if not client:
            logger.info(f"Redis client not available for {city}:{flag}")
            return None
        
        logger.info(f"Attempting to get cached places for {city}:{flag}")
        
        try:
            import json
            cache_key = self._get_place_cache_key(city, flag)
            
            # Try hot cache first
            try:
                logger.info(f"Attempting to read cache key: {cache_key}")
                cached_data = client.get(cache_key)
                logger.info(f"Cache data retrieved: {cached_data is not None}")
                if cached_data:
                    places_data = json.loads(cached_data)
                    logger.info(f"Parsed {len(places_data)} places from cache")
                    places = [Place.from_dict(place_dict) for place_dict in places_data]
                    # Mark places as from cache
                    for place in places:
                        place._from_cache = True
                    logger.info(f"Retrieved {len(places)} places from hot cache for {city}:{flag}, marked as from cache")
                    return places
            except Exception as redis_error:
                logger.error(f"Redis get operation failed for {city}:{flag}: {redis_error}")
                return None
            
            # Try stale cache
            try:
                stale_key = self._get_place_stale_key(city, flag)
                stale_data = client.get(stale_key)
                if stale_data:
                    places_data = json.loads(stale_data)
                    places = [Place.from_dict(place_dict) for place_dict in places_data]
                    logger.debug(f"Retrieved {len(places)} places from stale cache for {city}:{flag}")
                    return places
            except Exception as redis_error:
                logger.error(f"Redis stale get operation failed for {city}:{flag}: {redis_error}")
                return None
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached places for {city}:{flag}: {e}")
            return None
    
    def _warm_places_cache(self, city: str, flags: List[str], ttl: int = 3600) -> Dict[str, int]:
        """Warm up cache for specified flags using safe Redis implementation."""
        results = {}
        
        for flag in flags:
            try:
                # Fetch places for flag
                places = self.fetcher.fetch(city, category=flag, limit=100)
                
                if places:
                    # Save to database
                    try:
                        saved_count = save_places(places)
                        logger.info(f"Saved {saved_count} places to database for {city}:{flag}")
                    except Exception as e:
                        logger.warning(f"Failed to save places to database: {e}")
                    
                    # Cache places
                    if self._cache_places(city, flag, places, ttl):
                        results[flag] = len(places)
                        logger.info(f"Warmed cache for {city}:{flag} with {len(places)} places")
                    else:
                        results[flag] = 0
                        logger.warning(f"Failed to warm cache for {city}:{flag}")
                else:
                    results[flag] = 0
                    logger.warning(f"No places found for {city}:{flag}")
                    
            except Exception as e:
                logger.error(f"Error warming cache for {city}:{flag}: {e}")
                results[flag] = 0
        
        return results
    
    def _get_cache_stats(self, city: str) -> Dict[str, Any]:
        """Get cache statistics using safe Redis implementation."""
        client = self._get_redis_client()
        if not client:
            return {"error": "Redis not configured"}
        
        try:
            # Get index with safe Redis operations
            index_key = self._get_place_index_key(city)
            try:
                cached_flags = client.smembers(index_key)
            except Exception as redis_error:
                logger.error(f"Redis smembers operation failed for {city}: {redis_error}")
                return {"error": f"Redis operation failed: {redis_error}"}
            
            stats = {
                "city": city,
                "cached_flags": list(cached_flags),
                "total_flags": len(cached_flags),
                "redis_connected": True
            }
            
            # Count places in each flag with safe Redis operations
            total_places = 0
            for flag in cached_flags:
                flag_str = flag.decode('utf-8') if isinstance(flag, bytes) else flag
                cache_key = self._get_place_cache_key(city, flag_str)
                try:
                    cached_data = client.get(cache_key)
                    if cached_data:
                        import json
                        places_data = json.loads(cached_data)
                        total_places += len(places_data)
                except Exception as redis_error:
                    logger.error(f"Redis get operation failed for {city}:{flag_str}: {redis_error}")
                    continue
            
            stats["total_cached_places"] = total_places
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats for {city}: {e}")
            return {"error": str(e)}
    
    def get_places_by_flags(
        self, 
        city: str, 
        flags: List[str], 
        limit: Optional[int] = None,
        use_cache: bool = True
    ) -> List[Place]:
        """
        Get places by city and flags.
        
        Args:
            city: City name
            flags: List of flags to filter by
            limit: Optional limit on number of places
            use_cache: Whether to use cache
            
        Returns:
            List of Place objects
        """
        if not flags:
            return []
        
        # Если используем кэш, пробуем получить из него
        if use_cache:
            try:
                logger.info(f"Attempting to get places from cache for {city}:{flags}")
                # Пробуем получить из кэша для каждого флага
                cached_places = []
                for flag in flags:
                    places = self._get_cached_places(city, flag)
                    if places:
                        cached_places.extend(places)
                        logger.info(f"Got {len(places)} places from cache for flag {flag}")
                    else:
                        logger.info(f"No places in cache for flag {flag}")
                
                if cached_places:
                    # Дедупликация и фильтрация по флагам
                    unique_places = self._deduplicate_places(cached_places)
                    filtered_places = self._filter_places_by_flags(unique_places, flags)
                    
                    if limit:
                        filtered_places = filtered_places[:limit]
                    
                    # Debug: check if places have _from_cache flag
                    from_cache_count = sum(1 for p in filtered_places if hasattr(p, '_from_cache') and p._from_cache)
                    logger.info(f"Retrieved {len(filtered_places)} places from cache for {city}:{flags}, {from_cache_count} marked as from cache")
                    
                    # Если есть места из кэша, возвращаем их
                    if filtered_places:
                        logger.info(f"Returning {len(filtered_places)} places from cache")
                        return filtered_places
                    else:
                        logger.info("No places passed filtering, falling back to database")
            except Exception as e:
                logger.warning(f"Cache operation failed, falling back to database: {e}")
        
        # Если кэш не работает или пуст, получаем из БД
        try:
            engine = get_engine()
            places_data = get_places_by_flags(engine, flags, limit or 50)
            if places_data:
                logger.info(f"Retrieved {len(places_data)} places from database for {city}:{flags}")
                # Конвертируем в Place объекты
                places = []
                for place_dict in places_data:
                    place = Place(**place_dict)
                    places.append(place)
                return places
        except Exception as e:
            logger.warning(f"Failed to get places from database: {e}")
        
        # Если БД пуста, фетчим и сохраняем
        try:
            logger.info(f"Fetching places for {city}:{flags}")
            places = self._fetch_and_save_places(city, flags, limit)
            return places
        except Exception as e:
            logger.error(f"Failed to fetch places: {e}")
            return []
    
    def get_places_by_category(
        self, 
        city: str, 
        category: str, 
        limit: Optional[int] = None,
        use_cache: bool = True
    ) -> List[Place]:
        """
        Get places by city and category.
        
        Args:
            city: City name
            category: Category to filter by
            limit: Optional limit on number of places
            use_cache: Whether to use cache
            
        Returns:
            List of Place objects
        """
        # Получаем флаги для категории
        facets = categories_to_place_flags([category])
        flags = list(facets["flags"])
        
        if not flags:
            logger.warning(f"No flags found for category: {category}")
            return []
        
        return self.get_places_by_flags(city, flags, limit, use_cache)
    
    def get_all_places(
        self, 
        city: str, 
        limit: Optional[int] = None,
        use_cache: bool = True
    ) -> List[Place]:
        """
        Get all places for a city.
        
        Args:
            city: City name
            limit: Optional limit on number of places
            use_cache: Whether to use cache
            
        Returns:
            List of Place objects
        """
        # Получаем все места из БД
        try:
            engine = get_engine()
            places_data = get_all_places(engine, limit or 200)
            if places_data:
                logger.info(f"Retrieved {len(places_data)} places from database for {city}")
                # Конвертируем в Place объекты
                places = []
                for place_dict in places_data:
                    place = Place(**place_dict)
                    places.append(place)
                return places
        except Exception as e:
            logger.warning(f"Failed to get places from database: {e}")
        
        # Если БД пуста, фетчим все категории
        try:
            logger.info(f"Fetching all places for {city}")
            all_flags = self.fetcher.get_supported_categories()
            places = self._fetch_and_save_places(city, all_flags, limit)
            return places
        except Exception as e:
            logger.error(f"Failed to fetch all places: {e}")
            return []
    
    def _fetch_and_save_places(
        self, 
        city: str, 
        flags: List[str], 
        limit: Optional[int] = None
    ) -> List[Place]:
        """
        Fetch places and save to database and cache.
        
        Args:
            city: City name
            flags: List of flags to fetch
            limit: Optional limit on number of places
            
        Returns:
            List of Place objects
        """
        all_places = []
        
        for flag in flags:
            try:
                # Фетчим места для флага
                places = self.fetcher.fetch(city, category=flag, limit=limit)
                
                if places:
                    # Сохраняем в БД
                    try:
                        engine = get_engine()
                        # Конвертируем Place объекты в словари
                        places_dicts = [place.to_dict() for place in places]
                        saved_count = save_places(engine, places_dicts)
                        logger.info(f"Saved {saved_count} places to database for {city}:{flag}")
                    except Exception as e:
                        logger.warning(f"Failed to save places to database: {e}")
                    
                    # Кэшируем
                    try:
                        if self._cache_places(city, flag, places):
                            logger.info(f"Cached {len(places)} places for {city}:{flag}")
                        else:
                            logger.warning(f"Failed to cache places for {city}:{flag}")
                    except Exception as e:
                        logger.warning(f"Cache operation failed for {city}:{flag}: {e}")
                        # Continue without caching
                    
                    all_places.extend(places)
                
            except Exception as e:
                logger.error(f"Error fetching places for {city}:{flag}: {e}")
                continue
        
        # Дедупликация
        unique_places = self._deduplicate_places(all_places)
        
        # Применяем лимит
        if limit:
            unique_places = unique_places[:limit]
        
        return unique_places
    
    def _deduplicate_places(self, places: List[Place]) -> List[Place]:
        """Remove duplicate places based on identity_key."""
        logger.info(f"Deduplicating {len(places)} places")
        seen_keys = set()
        unique_places = []
        
        for place in places:
            identity_key = place.identity_key()
            if identity_key not in seen_keys:
                seen_keys.add(identity_key)
                unique_places.append(place)
        
        logger.info(f"Deduplication result: {len(unique_places)} unique places")
        return unique_places
    
    def _filter_places_by_flags(self, places: List[Place], flags: List[str]) -> List[Place]:
        """Filter places by flags."""
        logger.info(f"Filtering {len(places)} places by flags: {flags}")
        filtered_places = []
        
        for place in places:
            logger.info(f"Place {place.name} has flags: {place.flags}")
            # Если места взяты из кэша для определенного флага, они должны проходить фильтрацию
            if hasattr(place, '_from_cache') and place._from_cache:
                filtered_places.append(place)
                logger.info(f"Place {place.name} passed flag filtering (from cache)")
            elif any(flag in place.flags for flag in flags):
                filtered_places.append(place)
                logger.info(f"Place {place.name} passed flag filtering")
            else:
                logger.info(f"Place {place.name} failed flag filtering")
        
        logger.info(f"Filtering result: {len(filtered_places)} places passed")
        return filtered_places
    
    def warm_cache(self, city: str, flags: Optional[List[str]] = None, ttl: int = 3600) -> Dict[str, int]:
        """
        Warm up cache for specified flags.
        
        Args:
            city: City name
            flags: List of flags to warm up (if None, warm all)
            ttl: Cache TTL in seconds
            
        Returns:
            Dictionary with results for each flag
        """
        if flags is None:
            flags = self.fetcher.get_supported_categories()
        
        logger.info(f"Warming up cache for {city}:{flags}")
        return self._warm_places_cache(city, flags, ttl)
    
    def get_stats(self, city: str) -> Dict[str, Any]:
        """
        Get statistics about places and cache.
        
        Args:
            city: City name
            
        Returns:
            Dictionary with statistics
        """
        # Статистика БД
        try:
            engine = get_engine()
            db_stats = get_places_stats(engine)
        except Exception as e:
            logger.warning(f"Failed to get database stats: {e}")
            db_stats = {"error": str(e)}
        
        # Статистика кэша
        cache_stats = self._get_cache_stats(city)
        
        # Статистика fetcher'ов
        fetcher_stats = self.fetcher.get_fetcher_stats()
        
        return {
            "city": city,
            "database": db_stats,
            "cache": cache_stats,
            "fetchers": fetcher_stats,
            "timestamp": datetime.now().isoformat(),
        }
    
    def refresh_places(self, city: str, flags: Optional[List[str]] = None) -> Dict[str, int]:
        """
        Refresh places data by re-fetching and updating cache.
        
        Args:
            city: City name
            flags: List of flags to refresh (if None, refresh all)
            limit: Optional limit on number of places
            
        Returns:
            Dictionary with results for each flag
        """
        if flags is None:
            flags = self.fetcher.get_supported_categories()
        
        logger.info(f"Refreshing places for {city}:{flags}")
        
        results = {}
        for flag in flags:
            try:
                # Фетчим места
                places = self.fetcher.fetch(city, category=flag, limit=100)
                
                if places:
                    # Сохраняем в БД
                    try:
                        engine = get_engine()
                        places_dicts = [place.to_dict() for place in places]
                        saved_count = save_places(engine, places_dicts)
                    except Exception as e:
                        logger.warning(f"Failed to save places to database: {e}")
                        saved_count = 0
                    
                    # Обновляем кэш
                    if self._cache_places(city, flag, places):
                        results[flag] = len(places)
                        logger.info(f"Refreshed {len(places)} places for {city}:{flag}")
                    else:
                        results[flag] = 0
                        logger.warning(f"Failed to refresh cache for {city}:{flag}")
                else:
                    results[flag] = 0
                    logger.warning(f"No places found for {city}:{flag}")
                    
            except Exception as e:
                logger.error(f"Error refreshing places for {city}:{flag}: {e}")
                results[flag] = 0
        
        return results
