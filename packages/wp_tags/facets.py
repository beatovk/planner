"""
Facets mapping for events and places.
Provides unified interface for mapping content to flags and categories.
"""

from typing import Dict, Set, List
from .mapper import (
    flags_canonical,
    categories_to_facets,
    fallback_flags,
    map_event_to_flags,
    categories_to_place_flags,
    map_place_to_flags,
    get_cache_key,
    get_index_key,
)

# Re-export all functions from mapper
__all__ = [
    "flags_canonical",
    "categories_to_facets",
    "fallback_flags",
    "map_event_to_flags",
    "categories_to_place_flags",
    "map_place_to_flags",
    "get_cache_key",
    "get_index_key",
]
