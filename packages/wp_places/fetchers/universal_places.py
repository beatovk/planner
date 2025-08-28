"""
Universal places fetcher.
"""

from typing import List, Dict, Any, Optional
from packages.wp_models.place import Place


class UniversalPlacesFetcher:
    """Universal fetcher for places from various sources."""
    
    def __init__(self):
        """Initialize the fetcher."""
        pass
    
    def get_supported_categories(self) -> List[str]:
        """Get list of supported place categories."""
        return [
            "markets",
            "food_dining", 
            "art_exhibits",
            "entertainment",
            "wellness",
            "shopping"
        ]
    
    def fetch_places(self, city: str, category: str = None, limit: int = 50) -> List[Place]:
        """Fetch places from various sources."""
        # Mock implementation - replace with actual fetching logic
        places = []
        
        # Mock place data
        place = Place(
            id=1,
            name=f"Sample {category or 'general'} place in {city}",
            description=f"A sample {category or 'general'} place for testing",
            city=city,
            address="Sample Address",
            lat=13.7563,
            lon=100.5018,
            tags=[category] if category else ["sample"],
            flags=[category] if category else ["general"],
            popularity=5,
            source="mock"
        )
        places.append(place)
        
        return places[:limit]
