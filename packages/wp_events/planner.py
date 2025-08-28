"""
Event planning functionality.
"""

from typing import List, Dict, Any, Optional
from packages.wp_models.event import Event


def plan_week(
    city: str, tags: List[str], events: List[Event], max_per_day: int = 1
) -> List[Dict[str, Any]]:
    """Plan events for a week."""
    # Mock implementation - replace with actual planning logic
    schedule = []

    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    for i, day in enumerate(days):
        if i < len(events):
            event = events[i]
            schedule.append(
                {
                    "day": day,
                    "time": "evening",
                    "name": event.title,
                    "source": event.source,
                    "tags": event.tags,
                }
            )

    return schedule


def format_week_plan(items: List[Dict[str, Any]], city: str, tags: List[str]) -> str:
    """Format week plan as text."""
    lines = []
    lines.append(f"=== WEEK PLAN: {city} ===")
    lines.append(f"Tags: {', '.join(tags) if tags else '(no tags)'}")

    day_buckets = {}
    for item in items:
        day = item["day"]
        if day not in day_buckets:
            day_buckets[day] = []
        day_buckets[day].append(item)

    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for day in days:
        lines.append(f"\n{day}:")
        if day in day_buckets:
            for item in day_buckets[day]:
                tag_str = ", ".join(item["tags"])
                lines.append(
                    f"  - {item['time'].title()} — {item['name']} [{tag_str}] ({item['source']})"
                )
        else:
            lines.append("  - (free)")

    return "\n".join(lines)


def build_daily_cards(
    events: List[Dict[str, Any]], max_per_day: int = 6
) -> List[Dict[str, Any]]:
    """Build daily cards from events."""
    # Mock implementation - replace with actual card building logic
    days = []

    # Group events by day
    day_buckets = {}
    for event in events:
        date = event.get("date", "2024-01-01")
        if date not in day_buckets:
            day_buckets[date] = []
        day_buckets[date].append(event)

    # Create day cards
    for date, day_events in day_buckets.items():
        days.append({"day": date, "items": day_events[:max_per_day]})

    return days
