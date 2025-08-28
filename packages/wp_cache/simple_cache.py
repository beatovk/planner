"""
Simple in-memory cache implementation without Redis dependencies.
Provides TTL functionality and basic cache operations.
"""

import time
import json
import logging
from typing import Optional, Union, Dict, List, Any
from collections import OrderedDict

logger = logging.getLogger(__name__)


class SimpleCache:
    """
    Simple in-memory cache with TTL support.
    No external dependencies, lightweight and reliable.
    """
    
    def __init__(self, default_ttl: int = 3600, maxsize: int = 1000):
        """
        Initialize simple cache.
        
        Args:
            default_ttl: Default TTL in seconds
            maxsize: Maximum number of cached items
        """
        self.default_ttl = default_ttl
        self.maxsize = maxsize
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._timestamps: Dict[str, float] = {}
        self._ttls: Dict[str, int] = {}
        
        logger.info(f"SimpleCache initialized with TTL={default_ttl}s, maxsize={maxsize}")
    
    def _cleanup_expired(self):
        """Remove expired items from cache."""
        current_time = time.time()
        expired_keys = []
        
        for key, timestamp in self._timestamps.items():
            ttl = self._ttls.get(key, self.default_ttl)
            if current_time - timestamp > ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_key(key)
    
    def _remove_key(self, key: str):
        """Remove key from all internal structures."""
        if key in self._cache:
            del self._cache[key]
        if key in self._timestamps:
            del self._timestamps[key]
        if key in self._ttls:
            del self._ttls[key]
    
    def _ensure_capacity(self):
        """Ensure cache doesn't exceed maxsize by removing oldest items."""
        if len(self._cache) >= self.maxsize:
            # Remove oldest item (LRU)
            oldest_key = next(iter(self._cache))
            self._remove_key(oldest_key)
            logger.debug(f"Removed oldest key '{oldest_key}' to maintain capacity")
    
    def get_json(self, key: str) -> Optional[Union[Dict, List]]:
        """
        Get JSON value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value (dict/list) or None if not found/expired
        """
        self._cleanup_expired()
        
        if key in self._cache:
            # Move to end (LRU)
            self._cache.move_to_end(key)
            logger.debug(f"Cache hit for key: {key}")
            return self._cache[key]
        
        logger.debug(f"Cache miss for key: {key}")
        return None
    
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
        try:
            # Clean up expired items first
            self._cleanup_expired()
            
            # Ensure we have capacity
            self._ensure_capacity()
            
            # Set the value
            self._cache[key] = value
            self._timestamps[key] = time.time()
            self._ttls[key] = ttl if ttl is not None else self.default_ttl
            
            # Move to end (LRU)
            self._cache.move_to_end(key)
            
            logger.debug(f"Cached value for key: {key} with TTL: {self._ttls[key]}s")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def with_fallback(
        self,
        key: str,
        producer: callable,
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
        # Try to get from cache
        cached_value = self.get_json(key)
        if cached_value is not None:
            return cached_value
        
        # Cache miss - produce value
        logger.debug(f"Cache miss for key: {key}, producing value")
        try:
            value = producer()
            
            # Cache the result
            self.set_json(key, value, ttl)
            
            return value
            
        except Exception as e:
            logger.error(f"Producer failed for key {key}: {e}")
            # Return empty value in case of error
            if isinstance(producer(), dict):
                return {}
            else:
                return []
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False if not found
        """
        if key in self._cache:
            self._remove_key(key)
            logger.debug(f"Deleted key: {key}")
            return True
        
        return False
    
    def clear(self) -> None:
        """Clear all cached items."""
        self._cache.clear()
        self._timestamps.clear()
        self._ttls.clear()
        logger.info("Cache cleared")
    
    def size(self) -> int:
        """Get current cache size."""
        self._cleanup_expired()
        return len(self._cache)
    
    def keys(self) -> List[str]:
        """Get list of all cache keys (excluding expired)."""
        self._cleanup_expired()
        return list(self._cache.keys())
    
    def close(self) -> None:
        """Close cache (no-op for in-memory cache)."""
        logger.debug("SimpleCache closed (in-memory, no cleanup needed)")
    
    def __len__(self) -> int:
        """Get current cache size."""
        return self.size()
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache (excluding expired)."""
        return self.get_json(key) is not None
