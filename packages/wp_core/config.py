"""
Configuration module for the week planner application.
Centralizes all configuration settings using pydantic BaseSettings.
"""

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Server configuration
    PORT: int = Field(default=8000, alias="PORT", ge=1, le=65535)
    HOST: str = Field(default="0.0.0.0", alias="HOST")

    # Database configuration
    DB_URL: str = Field(default="sqlite:///data/wp_universal.db", alias="DATABASE_URL")
    DATABASE_ECHO: bool = Field(default=False, alias="DATABASE_ECHO")

    # Redis configuration - REMOVED
    # Redis dependencies removed - using simple in-memory cache

    # Cache configuration
    CACHE_TTL: int = Field(default=3600, alias="CACHE_TTL")  # Default: 1 hour
    CACHE_BYPASS: bool = Field(default=False, alias="CACHE_BYPASS")
    CACHE_LONG_TTL: int = Field(
        default=7200, alias="CACHE_LONG_TTL"
    )  # Default: 2 hours
    CACHE_SHORT_TTL: int = Field(
        default=1800, alias="CACHE_SHORT_TTL"
    )  # Default: 30 minutes

    # Application configuration
    APP_NAME: str = Field(default="Week Planner", alias="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", alias="APP_VERSION")
    DEBUG: bool = Field(default=False, alias="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", alias="LOG_LEVEL")

    # Feature flags
    EVENTS_DISABLED: bool = Field(default=False, alias="EVENTS_DISABLED")
    WP_CACHE_DISABLE: bool = Field(default=False, alias="WP_CACHE_DISABLE")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Global settings instance
settings = Settings()

# Cache key patterns
CACHE_VERSION = "v2"
CACHE_KEY_PREFIX = f"{CACHE_VERSION}:places"


def get_cache_key(
    city: str, flag: Optional[str] = None, query: Optional[str] = None, limit: int = 50
) -> str:
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
        return settings.CACHE_LONG_TTL
    elif cache_type == "short":
        return settings.CACHE_SHORT_TTL
    else:
        return settings.CACHE_TTL


def is_cache_enabled() -> bool:
    """Check if caching is enabled."""
    return not (settings.CACHE_BYPASS or settings.WP_CACHE_DISABLE)


def is_redis_available() -> bool:
    """Check if Redis is configured and available."""
    # Redis removed - using simple in-memory cache
    return False


def get_config_summary() -> dict:
    """Get configuration summary for debugging."""
    return {
        "server": {
            "port": settings.PORT,
            "host": settings.HOST,
        },
        "database": {
            "url": settings.DB_URL,
            "echo": settings.DATABASE_ECHO,
        },
        "redis": {
            "note": "Redis removed - using simple in-memory cache",
            "available": False,
        },
        "cache": {
            "enabled": is_cache_enabled(),
            "ttl": settings.CACHE_TTL,
            "long_ttl": settings.CACHE_LONG_TTL,
            "short_ttl": settings.CACHE_SHORT_TTL,
            "bypass": settings.CACHE_BYPASS,
        },
        "app": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "debug": settings.DEBUG,
            "log_level": settings.LOG_LEVEL,
        },
        "features": {
            "events_disabled": settings.EVENTS_DISABLED,
            "cache_disabled": settings.WP_CACHE_DISABLE,
        },
    }


# Backward compatibility aliases
PORT = settings.PORT
HOST = settings.HOST
DATABASE_URL = settings.DB_URL
# REDIS_URL removed - using simple in-memory cache
CACHE_TTL = settings.CACHE_TTL
CACHE_BYPASS = settings.CACHE_BYPASS
APP_NAME = settings.APP_NAME
APP_VERSION = settings.APP_VERSION
DEBUG = settings.DEBUG
LOG_LEVEL = settings.LOG_LEVEL
