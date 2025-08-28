"""
Live events functionality.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


def load_source_map(sources_file: Path) -> Dict[str, Any]:
    """Load source mapping from JSON file."""
    try:
        with open(sources_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load sources: {e}")
        return {}


def fetch_for_categories(source_map: Dict[str, Any], category_ids: List[str], 
                        date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch events for specified categories."""
    # Mock implementation - replace with actual fetching logic
    events = []
    
    for category_id in category_ids:
        # Mock event data
        event = {
            "title": f"Sample {category_id} event",
            "subtitle": f"Category: {category_id}",
            "date": date_from or "2024-01-01",
            "end": date_to or "2024-01-01",
            "time": "19:00",
            "source": "mock",
            "url": "https://example.com",
            "venue": "Sample Venue",
            "desc": f"This is a sample event for category {category_id}",
            "popularity": 5,
            "price_min": 0,
            "rating": 4.5,
            "image": None,
            "category": category_id,
            "tags": [category_id]
        }
        events.append(event)
    
    return events


def fetch_from_source(source: str) -> List[Dict[str, Any]]:
    """Fetch events from a specific source."""
    # Mock implementation - replace with actual source fetching logic
    events = []
    
    # Mock event data
    event = {
        "title": f"Sample event from {source}",
        "subtitle": f"Source: {source}",
        "date": "2024-01-01",
        "end": "2024-01-01",
        "time": "19:00",
        "source": source,
        "url": "https://example.com",
        "venue": "Sample Venue",
        "desc": f"This is a sample event from source {source}",
        "popularity": 5,
        "price_min": 0,
        "rating": 4.5,
        "image": None,
        "category": "general",
        "tags": ["sample", source]
    }
    events.append(event)
    
    return events
