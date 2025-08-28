"""
Configuration module for the week planner application.
Centralizes all configuration settings including cache, Redis, and application settings.
"""

import os
from typing import Optional

# Cache configuration
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # Default: 1 hour
CACHE_BYPASS = os.getenv("CACHE_BYPASS", "0").lower() in ("1", "true", "yes", "on")
CACHE_LONG_TTL = int(os.getenv("CACHE_LONG_TTL", "7200"))  # Default: 2 hours
CACHE_SHORT_TTL = int(os.getenv("CACHE_SHORT_TTL", "1800"))  # Default: 30 minutes

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_TIMEOUT = int(os.getenv("REDIS_TIMEOUT", "5"))  # seconds

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/places.db")
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "0").lower() in ("1", "true", "yes", "on")

# Application configuration
APP_NAME = os.getenv("APP_NAME", "Week Planner")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEBUG = os.getenv("DEBUG", "0").lower() in ("1", "true", "yes", "on")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Cache key patterns
CACHE_VERSION = "v2"
CACHE_KEY_PREFIX = f"{CACHE_VERSION}:places"

def get_cache_key(city: str, flag: Optional[str] = None, 
                  query: Optional[str] = None, limit: int = 50) -> str:
    """
    Generate standardized cache key.
    
    Args:
        city: City name
        flag: Optional flag/category
        query: Optional search query
        limit: Result limit
        
    Returns:
        Standardized cache key
    """
    city = city.lower()
    
    if flag:
        # Key pattern: v2:{city}:flag:{flag}
        return f"{CACHE_KEY_PREFIX}:{city}:flag:{flag}"
    elif query:
        # Key pattern: v2:{city}:search:{query}:{limit}
        # Normalize query for consistent keys
        normalized_query = query.lower().strip().replace(" ", "_")
        return f"{CACHE_KEY_PREFIX}:{city}:search:{normalized_query}:{limit}"
    else:
        # Key pattern: v2:{city}:all
        return f"{CACHE_KEY_PREFIX}:{city}:all"

def get_cache_ttl(cache_type: str = "default") -> int:
    """
    Get TTL for specific cache type.
    
    Args:
        cache_type: Type of cache ("default", "long", "short")
        
    Returns:
        TTL in seconds
    """
    if cache_type == "long":
        return CACHE_LONG_TTL
    elif cache_type == "short":
        return CACHE_SHORT_TTL
    else:
        return CACHE_TTL

def is_cache_enabled() -> bool:
    """Check if caching is enabled."""
    return not CACHE_BYPASS

def is_redis_available() -> bool:
    """Check if Redis is configured and available."""
    return bool(REDIS_URL and REDIS_URL != "redis://localhost:6379/0")

def get_config_summary() -> dict:
    """Get configuration summary for debugging."""
    return {
        "cache": {
            "enabled": is_cache_enabled(),
            "ttl": CACHE_TTL,
            "long_ttl": CACHE_LONG_TTL,
            "short_ttl": CACHE_SHORT_TTL,
            "bypass": CACHE_BYPASS,
            "version": CACHE_VERSION
        },
        "redis": {
            "url": REDIS_URL,
            "host": REDIS_HOST,
            "port": REDIS_PORT,
            "db": REDIS_DB,
            "timeout": REDIS_TIMEOUT,
            "available": is_redis_available()
        },
        "database": {
            "url": DATABASE_URL,
            "echo": DATABASE_ECHO
        },
        "app": {
            "name": APP_NAME,
            "version": APP_VERSION,
            "debug": DEBUG,
            "log_level": LOG_LEVEL
        },
        "server": {
            "host": HOST,
            "port": PORT
        }
    }
