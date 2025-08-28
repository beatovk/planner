"""
Core types for the Week Planner system.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class ScheduledItem:
    """Represents a scheduled item in a week plan."""

    day: str
    time: str
    name: str
    source: str
    tags: List[str]
