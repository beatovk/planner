import warnings
warnings.warn("core.events is deprecated; use packages.wp_models.event", DeprecationWarning)

from packages.wp_models.event import Event  # noqa: F401
