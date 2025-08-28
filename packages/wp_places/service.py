#!/usr/bin/env python
"""
Places service that combines fetchers, database, and cache.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from packages.wp_places.fetchers.universal_places import UniversalPlacesFetcher
from packages.wp_places.dao import (
    init_schema, save_places, get_places_by_flags, 
    get_all_places, get_places_stats, load_from_json, search_by_category, search, get_search_stats
)
from packages.wp_core.db import get_engine
from packages.wp_cache.cache import get_cache_client
from packages.wp_core.config import get_cache_key, get_cache_ttl, is_cache_enabled
from packages.wp_models.place import Place
from packages.wp_tags.mapper import categories_to_place_flags
import logging
logger = logging.getLogger("places")


class PlacesService:
    """Service for managing places data."""
    
    def __init__(self):
        self.fetcher = UniversalPlacesFetcher()
        self._cache_client = get_cache_client()
        self._ensure_db_initialized()
    
    def _ensure_db_initialized(self):
        """Ensure places database is initialized."""
        try:
            engine = get_engine()
            init_schema(engine)
            logger.info("Places database schema initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize places database: {e}")
    
    def _get_place_cache_key(self, city: str, flag: str) -> str:
        """Generate standardized cache key for places."""
        return get_cache_key(city, flag)
    
    def _get_search_cache_key(self, city: str, query: str, limit: int = 20) -> str:
        """Generate standardized cache key for search results."""
        return get_cache_key(city, query=query, limit=limit)
    
    def _cache_places(self, city: str, flag: str, places: List[Place], ttl: int = 3600) -> bool:
        """Cache places using unified cache client."""
        if not is_cache_enabled():
            logger.debug(f"Cache disabled, skipping cache for {city}:{flag}")
            return False
        
        try:
            cache_key = self._get_place_cache_key(city, flag)
            
            # Convert places to dict format for caching
            places_data = []
            for place in places:
                place_dict = place.to_dict()
                # Remove fields not needed in cache
                place_dict.pop("created_at", None)
                place_dict.pop("updated_at", None)
                places_data.append(place_dict)
            
            # Cache places using unified cache client
            success = self._cache_client.set_json(cache_key, places_data, ttl)
            
            if success:
                logger.debug(f"Cached {len(places)} places for {city}:{flag}")
            else:
                logger.warning(f"Failed to cache places for {city}:{flag}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error caching places for {city}:{flag}: {e}")
            return False
    
    def _get_cached_places(self, city: str, flag: str) -> Optional[List[Place]]:
        """Get places from cache using unified cache client."""
        if not is_cache_enabled():
            logger.debug(f"Cache disabled for {city}:{flag}")
            return None
        
        try:
            cache_key = self._get_place_cache_key(city, flag)
            logger.debug(f"Attempting to get cached places for {city}:{flag}")
            
            # Get cached data using unified cache client
            cached_data = self._cache_client.get_json(cache_key)
            
            if cached_data is not None:
                logger.info(f"Cache hit for {city}:{flag}")
                
                # Convert back to Place objects
                places = []
                for place_dict in cached_data:
                    try:
                        place = Place(**place_dict)
                        places.append(place)
                    except Exception as e:
                        logger.warning(f"Failed to create Place object from cache: {e}")
                        continue
                
                logger.info(f"Retrieved {len(places)} places from cache for {city}:{flag}")
                return places
            else:
                logger.debug(f"Cache miss for {city}:{flag}")
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
        """Get cache statistics using unified cache client."""
        if not is_cache_enabled():
            return {
                "city": city,
                "cache_enabled": False,
                "error": "Cache disabled"
            }
        
        try:
            # Get cache statistics from unified cache client
            cache_stats = self._cache_client.get_stats()
            
            # Get cached flags for the city
            pattern = f"{get_cache_key(city)}:*"
            cached_keys = []
            
            # Try to get keys matching the pattern
            try:
                # This is a simplified approach - in production you might want to maintain an index
                # For now, we'll return basic cache stats
                pass
            except Exception as e:
                logger.warning(f"Failed to get cached keys for {city}: {e}")
            
            return {
                "city": city,
                "cache_enabled": True,
                "cache_stats": cache_stats,
                "cached_keys_pattern": pattern,
                "total_cached": len(cached_keys) if cached_keys else 0
            }
                
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

    def search_places(self, query: str, limit: int = 20, category: Optional[str] = None, city: str = "bangkok") -> List[Place]:
        """
        Поиск мест с использованием FTS5 и кэширования
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
            category: Опциональная категория для фильтрации
            city: Город для поиска
            
        Returns:
            Список Place объектов
        """
        # Пытаемся получить из кэша
        if is_cache_enabled():
            cache_key = self._get_search_cache_key(city, query, limit)
            cached_places = self._cache_client.get_json(cache_key)
            
            if cached_places:
                logger.info(f"Cache hit for search query: {query}")
                # Конвертируем обратно в Place объекты
                places = []
                for place_dict in cached_places:
                    try:
                        place = Place(**place_dict)
                        places.append(place)
                    except Exception as e:
                        logger.warning(f"Failed to create Place object from cache: {e}")
                        continue
                return places
        
        # Кэш miss - выполняем поиск
        logger.debug(f"Cache miss for search query: {query}, performing FTS5 search")
        try:
            engine = get_engine()
            
            if category:
                places_data = search_by_category(engine, query, category, limit)
            else:
                places_data = search(engine, query, limit)
            
            if not places_data:
                logger.info(f"No places found for query: {query}")
                return []
            
            # Конвертируем в Place объекты
            places = []
            for place_dict in places_data:
                try:
                    place = Place(**place_dict)
                    places.append(place)
                except Exception as e:
                    logger.warning(f"Failed to create Place object: {e}")
                    continue
            
            # Кэшируем результаты поиска
            if is_cache_enabled() and places:
                cache_key = self._get_search_cache_key(city, query, limit)
                places_data_for_cache = [place.to_dict() for place in places]
                self._cache_client.set_json(cache_key, places_data_for_cache, get_cache_ttl("short"))
                logger.debug(f"Cached search results for query: {query}")
            
            logger.info(f"Found {len(places)} places for query: {query}")
            return places
            
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return []

    def get_search_statistics(self) -> Dict[str, Any]:
        """Получение статистики по поиску"""
        try:
            engine = get_engine()
            return get_search_stats(engine)
        except Exception as e:
            logger.error(f"Failed to get search statistics: {e}")
            return {"error": str(e)}
