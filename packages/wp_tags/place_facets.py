#!/usr/bin/env python
"""
Place to facets mapping for place queries - thin wrapper around wp_tags/facets.py.
"""

import re
from typing import Dict, Set, List
from packages.wp_core.logging import logger


def map_place_to_flags(place: dict) -> list[str]:
    """
    Универсальный маппинг мест → флаги на основе контента.
    Delegates to the unified mapper in wp_tags/facets.py.

    Args:
        place: Словарь места с полями name, description, tags, area

    Returns:
        Отсортированный список флагов для места
    """
    try:
        # Import the unified mapper using absolute path
        from packages.wp_tags.facets import map_event_to_flags

        # Use the same logic for places as events
        return map_event_to_flags(place)
    except ImportError:
        # Fallback to local implementation if import fails
        return _fallback_map_place_to_flags(place)


def _fallback_map_place_to_flags(place: dict) -> list[str]:
    """
    Minimal fallback implementation if unified mapper is not available.
    Only basic mapping, delegates to unified mapper when possible.
    """
    if not place:
        return []

    # Basic fallback - just return empty list to force delegation
    # The main implementation should always use the unified mapper
    logger.warning("Using fallback tag mapper - unified mapper not available")
    return []


def categories_to_place_flags(selected_category_ids: list[str]) -> Dict[str, Set[str]]:
    """
    Translate user categories into place cache/search facets.
    Delegates to the unified mapper in wp_tags/facets.py.

    Args:
        selected_category_ids: List of category IDs from user selection

    Returns:
        Dict with "flags" and "categories" sets
    """
    try:
        # Import the unified mapper using absolute path
        from packages.wp_tags.facets import categories_to_facets

        # Use the same logic for places as events
        return categories_to_facets(selected_category_ids)
    except ImportError:
        # Fallback to local implementation if import fails
        return _fallback_categories_to_place_flags(selected_category_ids)


def _fallback_categories_to_place_flags(
    selected_category_ids: list[str],
) -> Dict[str, Set[str]]:
    """
    Minimal fallback implementation if unified mapper is not available.
    Only basic mapping, delegates to unified mapper when possible.
    """
    # Basic fallback - just return empty sets to force delegation
    # The main implementation should always use the unified mapper
    logger.warning("Using fallback category mapper - unified mapper not available")
    return {"flags": set(), "categories": set()}


def get_place_cache_key(city: str, flag: str) -> str:
    """
    Generate standardized cache key for places (v2 format).

    Args:
        city: City name (e.g., "bangkok")
        flag: Flag name (e.g., "art", "music")

    Returns:
        Cache key string
    """
    from packages.wp_core.config import get_cache_key

    return get_cache_key(city, flag)


def get_place_index_key(city: str) -> str:
    """
    Generate standardized cache key for place index (v2 format).

    Args:
        city: City name (e.g., "bangkok")

    Returns:
        Cache key string
    """
    from packages.wp_core.config import get_cache_key

    return get_cache_key(city)
