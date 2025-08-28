import warnings
warnings.warn("core.db is deprecated; use packages.wp_core.db", DeprecationWarning)
from packages.wp_core.db import get_db_url, get_engine, healthcheck, init_db  # noqa

def seed_sample_art_events():
    """Seed sample art events."""
    # Mock implementation
    pass
