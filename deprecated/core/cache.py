"""
DEPRECATED: This module is deprecated. Use packages.wp_cache instead.
"""

import warnings
from packages.wp_cache.cache import *

warnings.warn(
    "core.cache is deprecated; use packages.wp_cache instead", 
    DeprecationWarning, 
    stacklevel=2
)
