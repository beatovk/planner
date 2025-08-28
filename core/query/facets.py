import warnings
warnings.warn("core/query/facets.py is deprecated; use packages.wp_tags.mapper", DeprecationWarning)

from packages.wp_tags.mapper import (
    flags_canonical, categories_to_facets, fallback_flags, map_event_to_flags,
    categories_to_place_flags, map_place_to_flags,
    get_cache_key, get_index_key,
)  # noqa
