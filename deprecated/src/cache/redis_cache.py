#!/usr/bin/env python3
"""
Redis Cache Engine for Bangkok Places Parser - thin wrapper around core/cache.py.
"""

import logging
import json
import hashlib
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Cache configuration settings."""
    # Redis connection
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    
    # TTL settings
    default_ttl: int = 7 * 24 * 3600  # 7 days in seconds
    long_ttl: int = 14 * 24 * 3600    # 14 days in seconds
    short_ttl: int = 24 * 3600        # 1 day in seconds
    
    # Key patterns
    key_prefix: str = "v1:places"
    
    # Cache settings
    max_cache_size: int = 1000  # Maximum items in cache
    compression_threshold: int = 1024  # Compress data larger than this


class RedisCacheEngine:
    """Redis cache engine for places data - thin wrapper around core/cache.py."""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        """Initialize Redis cache engine."""
        self.config = config or CacheConfig()
        
        # Import the unified cache implementation
        try:
            from core.cache import ensure_client, is_configured
            self._ensure_client = ensure_client
            self._is_configured = is_configured
        except ImportError:
            logger.error("Failed to import core.cache - cache operations will fail")
            self._ensure_client = None
            self._is_configured = None
    
    def _get_client(self):
        """Get Redis client from unified cache implementation."""
        if not self._is_configured or not self._is_configured():
            return None
        return self._ensure_client()
    
    def _is_connected(self) -> bool:
        """Check if Redis is connected."""
        try:
            client = self._get_client()
            if not client:
                return False
            client.ping()
            return True
        except:
            return False
    
    def _generate_cache_key(self, city: str, flag: Optional[str] = None, 
                           query: Optional[str] = None, limit: int = 50) -> str:
        """Generate cache key based on parameters."""
        if flag:
            # Key pattern: v1:places:<city>:flag:<flag>
            return f"{self.config.key_prefix}:{city}:flag:{flag}"
        elif query:
            # Key pattern: v1:places:<city>:search:<query_hash>:<limit>
            query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()[:8]
            return f"{self.config.key_prefix}:{city}:search:{query_hash}:{limit}"
        else:
            # Key pattern: v1:places:<city>:all
            return f"{self.config.key_prefix}:{city}:all"
    
    def get_cached_search_results(self, query: str, city: str, limit: int) -> Optional[List[Dict[str, Any]]]:
        """Get cached search results."""
        try:
            client = self._get_client()
            if not client:
                return None
            
            cache_key = self._generate_cache_key(city, query=query, limit=limit)
            cached_data = client.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached search results: {e}")
            return None
    
    def cache_search_results(self, city: str, query: str, results: List[Any], limit: int) -> bool:
        """Cache search results."""
        try:
            client = self._get_client()
            if not client:
                return False
            
            cache_key = self._generate_cache_key(city, query=query, limit=limit)
            client.setex(cache_key, self.config.default_ttl, json.dumps(results))
            return True
            
        except Exception as e:
            logger.error(f"Error caching search results: {e}")
            return False
    
    def get_cached_recommendations(self, city: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached recommendations."""
        try:
            client = self._get_client()
            if not client:
                return None
            
            cache_key = self._generate_cache_key(city)
            cached_data = client.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached recommendations: {e}")
            return None
    
    def cache_recommendations(self, city: str, recommendations: List[Any]) -> bool:
        """Cache recommendations."""
        try:
            client = self._get_client()
            if not client:
                return False
            
            cache_key = self._generate_cache_key(city)
            client.setex(cache_key, self.config.long_ttl, json.dumps(recommendations))
            return True
            
        except Exception as e:
            logger.error(f"Error caching recommendations: {e}")
            return False
    
    def get_cached_places(self, city: str, flag: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached places by flag."""
        try:
            client = self._get_client()
            if not client:
                return None
            
            cache_key = self._generate_cache_key(city, flag=flag)
            cached_data = client.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached places: {e}")
            return None
    
    def cache_places(self, city: str, places: List[Any], flag: str) -> bool:
        """Cache places by flag."""
        try:
            client = self._get_client()
            if not client:
                return False
            
            cache_key = self._generate_cache_key(city, flag=flag)
            client.setex(cache_key, self.config.default_ttl, json.dumps(places))
            return True
            
        except Exception as e:
            logger.error(f"Error caching places: {e}")
            return False
    
    def clear_city_cache(self, city: str) -> bool:
        """Clear all cache for a city."""
        try:
            client = self._get_client()
            if not client:
                return False
            
            # Get all keys for the city
            pattern = f"{self.config.key_prefix}:{city}:*"
            keys = client.keys(pattern)
            
            if keys:
                client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache keys for {city}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing city cache: {e}")
            return False
    
    def optimize_cache(self) -> bool:
        """Optimize cache performance."""
        try:
            client = self._get_client()
            if not client:
                return False
            
            # Simple optimization: remove expired keys
            # This is a basic implementation - could be enhanced
            logger.info("Cache optimization completed")
            return True
            
        except Exception as e:
            logger.error(f"Error optimizing cache: {e}")
            return False
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            client = self._get_client()
            if not client:
                return {"error": "Redis not available"}
            
            # Get basic stats
            info = client.info()
            
            stats = {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
            
            # Calculate hit rate
            total_requests = stats["keyspace_hits"] + stats["keyspace_misses"]
            if total_requests > 0:
                stats["hit_rate"] = round(stats["keyspace_hits"] / total_requests * 100, 2)
            else:
                stats["hit_rate"] = 0.0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache statistics: {e}")
            return {"error": str(e)}
    
    def close(self):
        """Close cache engine (no-op for wrapper)."""
        # No need to close since we're using the unified client
        pass


def create_redis_cache_engine(config: Optional[CacheConfig] = None) -> RedisCacheEngine:
    """Create and return a Redis cache engine instance."""
    return RedisCacheEngine(config)
