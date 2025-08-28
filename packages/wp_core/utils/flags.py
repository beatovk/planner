import os


def events_disabled() -> bool:
    """Check if events are disabled via environment variable.
    
    Returns:
        bool: True if WP_DISABLE_EVENTS=1, False otherwise
    """
    return os.getenv("WP_DISABLE_EVENTS", "0") == "1"
