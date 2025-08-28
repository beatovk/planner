import warnings
warnings.warn("core.models_places is deprecated; use packages.wp_models.place", DeprecationWarning)

from packages.wp_models.place import Place  # noqa: F401

__all__ = [
    "Place",
]
