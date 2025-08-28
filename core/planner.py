import warnings
warnings.warn("core.planner is deprecated; use packages.wp_events.service", DeprecationWarning)

from packages.wp_events.service import (
    find_candidates,
    build_week_cards_from_places,
    build_day_cards_from_places,
)  # noqa
