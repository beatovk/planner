"""
Test that events and places use a single tag mapper.
"""

import pytest
from packages.wp_tags.mapper import map_event_to_flags, map_place_to_flags


def test_tag_mapper_functions_exist():
    """Test that tag mapper functions exist and are callable."""
    assert callable(map_event_to_flags)
    assert callable(map_place_to_flags)


def test_event_tag_mapping():
    """Test that event tag mapping works."""
    # Test with sample event data
    event_data = {
        "title": "Food Festival",
        "categories": ["food", "festival"],
        "tags": ["restaurant", "thai"]
    }
    
    flags = map_event_to_flags(event_data)
    assert isinstance(flags, list)
    assert len(flags) > 0
    
    # Should contain food-related flags
    food_flags = [f for f in flags if "food" in f.lower() or "dining" in f.lower()]
    assert len(food_flags) > 0


def test_place_tag_mapping():
    """Test that place tag mapping works."""
    # Test with sample place data
    place_data = {
        "name": "Central Market",
        "tags": ["market", "shopping"],
        "flags": []
    }
    
    flags = map_place_to_flags(place_data)
    assert isinstance(flags, list)
    assert len(flags) > 0
    
    # Should contain market-related flags
    market_flags = [f for f in flags if "market" in f.lower() or "shopping" in f.lower()]
    assert len(market_flags) > 0


def test_consistent_flag_format():
    """Test that both mappers return consistent flag format."""
    event_data = {"title": "Art Gallery Opening", "categories": ["art"]}
    place_data = {"name": "Art Gallery", "tags": ["art", "gallery"]}
    
    event_flags = map_event_to_flags(event_data)
    place_flags = map_place_to_flags(place_data)
    
    # Both should return flags in the same format
    assert isinstance(event_flags, list)
    assert isinstance(place_flags, list)
    
    # Flags should be strings
    for flag in event_flags + place_flags:
        assert isinstance(flag, str)
        assert len(flag) > 0


def test_mapper_handles_empty_input():
    """Test that mappers handle empty or None input gracefully."""
    # Test with empty data
    empty_event = {}
    empty_place = {}
    
    event_flags = map_event_to_flags(empty_event)
    place_flags = map_place_to_flags(empty_place)
    
    # Should return empty list, not None
    assert event_flags == []
    assert place_flags == []
    
    # Test with None
    event_flags_none = map_event_to_flags(None)
    place_flags_none = map_place_to_flags(None)
    
    assert event_flags_none == []
    assert place_flags_none == []
