"""
Logging configuration for the week planner application.
Provides centralized logging setup and configuration.
"""

import logging
import os
from packages.wp_core.config import LOG_LEVEL

# Configure logging level from environment
log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)

# Configure basic logging
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# Create logger instances for different modules
def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified module.

    Args:
        name: Module name (e.g., "places", "cache", "fetcher")

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(f"wp.{name}")
    logger.setLevel(log_level)

    # Add NullHandler if no handlers configured
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())

    return logger


# Common loggers
places_logger = get_logger("places")
cache_logger = get_logger("cache")
fetcher_logger = get_logger("fetcher")
db_logger = get_logger("db")
api_logger = get_logger("api")

# Legacy logger for backward compatibility
logger = places_logger

__all__ = [
    "logger",
    "places_logger",
    "cache_logger",
    "fetcher_logger",
    "db_logger",
    "api_logger",
    "get_logger",
]
