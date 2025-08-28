import warnings
warnings.warn("core.models is deprecated; use packages.wp_models", DeprecationWarning)

from packages.wp_models.event import Event  # noqa: F401
from packages.wp_models.place import Place  # noqa: F401

__all__ = [
    "Place",
]
