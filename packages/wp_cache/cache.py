"""
Cache client for the week planner application.
Uses simple in-memory cache without external dependencies.
Provides JSON serialization/deserialization and TTL support.
"""

import json
import logging
from typing import Optional, Union, Dict, List, Callable
from packages.wp_cache.simple_cache import SimpleCache

logger = logging.getLogger(__name__)


class CacheClient:
    """
    Cache client with JSON support and TTL.
    Uses simple in-memory cache - lightweight and reliable.
    """
    
    def __init__(self, default_ttl: int = 3600):
        """
        Initialize cache client.
        
        Args:
            default_ttl: Default TTL in seconds for cached items
        """
        self.default_ttl = default_ttl
        self._cache = SimpleCache(default_ttl=default_ttl)
        logger.info(f"Cache client initialized with SimpleCache (TTL={default_ttl}s)")
    
    def get_json(self, key: str) -> Optional[Union[Dict, List]]:
        """
        Get JSON value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value (dict/list) or None if not found
        """
        return self._cache.get_json(key)
    
    def set_json(self, key: str, value: Union[Dict, List], ttl: Optional[int] = None) -> bool:
        """
        Set JSON value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (dict or list)
            ttl: TTL in seconds (uses default if None)
            
        Returns:
            True if successful
        """
        return self._cache.set_json(key, value, ttl)
    
    def with_fallback(
        self,
        key: str,
        producer: Callable[[], Union[Dict, List]],
        ttl: Optional[int] = None
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
        return self._cache.with_fallback(key, producer, ttl)
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False if not found
        """
        return self._cache.delete(key)
    
    def clear(self) -> None:
        """Clear all cached items."""
        self._cache.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        return self._cache.size()
    
    def keys(self) -> List[str]:
        """Get list of all cache keys."""
        return self._cache.keys()
    
    def close(self) -> None:
        """Close cache (no-op for in-memory cache)."""
        self._cache.close()
    
    def __len__(self) -> int:
        """Get current cache size."""
        return len(self._cache)
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache."""
        return key in self._cache


def get_cache_client(default_ttl: int = 3600) -> CacheClient:
    """
    Get a cache client instance.
    
    Args:
        default_ttl: Default TTL in seconds
        
    Returns:
        CacheClient instance
    """
    return CacheClient(default_ttl)
