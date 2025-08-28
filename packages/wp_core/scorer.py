"""
Scoring functions for events and places.
"""

from typing import Dict, Any


def coolness(event: Dict[str, Any]) -> float:
    """Calculate coolness score for an event."""
    score = 0.0

    # Base score from popularity
    popularity = event.get("popularity", 0)
    score += popularity * 0.5

    # Bonus for rating
    rating = event.get("rating", 0)
    score += rating * 0.3

    # Bonus for having image
    if event.get("image"):
        score += 0.2

    # Bonus for venue
    if event.get("venue"):
        score += 0.1

    return score


def boost(event: Dict[str, Any]) -> float:
    """Calculate boosted score for an event."""
    base_score = coolness(event)

    # Additional boost factors
    boost_multiplier = 1.0

    # Boost for high popularity
    if event.get("popularity", 0) > 7:
        boost_multiplier += 0.2

    # Boost for high rating
    if event.get("rating", 0) > 4.5:
        boost_multiplier += 0.1

    return base_score * boost_multiplier
