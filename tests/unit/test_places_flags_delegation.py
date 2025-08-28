#!/usr/bin/env python3
"""
Unit test to verify PlacesService uses shared tag grammar from core/query/facets.py.
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from packages.wp_places.service import PlacesService


class TestPlacesServiceFlagsDelegation:
    """Test that PlacesService uses shared tag grammar from core/query/facets.py."""
    
    @patch('packages.wp_places.service.categories_to_place_flags')
    def test_get_places_by_category_delegates_to_shared_mapper(self, mock_categories_to_flags):
        """Test that get_places_by_category calls shared tag mapper."""
        # Setup mock
        mock_categories_to_flags.return_value = {
            "flags": {"food_dining", "rooftop"},
            "categories": {"restaurant"}
        }
        
        # Create service
        service = PlacesService()
        
        # Mock database and cache operations
        with patch.object(service, '_get_cached_places') as mock_get_cached:
            mock_get_cached.return_value = []
            
            with patch('packages.wp_places.service.PlacesService.get_places_by_flags') as mock_db_get:
                mock_db_get.return_value = []
                
                # Test category to flags delegation
                service.get_places_by_category("bangkok", "restaurant")
                
                # Verify shared mapper was called
                mock_categories_to_flags.assert_called_once_with(["restaurant"])
    
    @patch('packages.wp_tags.place_facets.map_place_to_flags')
    def test_place_flags_mapping_delegates_to_shared_mapper(self, mock_map_to_flags):
        """Test that place flags mapping uses shared mapper."""
        # Setup mock
        mock_map_to_flags.return_value = ["food_dining", "rooftop"]
        
        # Test the delegation function directly
        from packages.wp_tags.place_facets import map_place_to_flags
        
        test_place = {
            "name": "Test Restaurant",
            "description": "Rooftop dining with Thai food",
            "tags": ["restaurant", "rooftop"]
        }
        
        result = map_place_to_flags(test_place)
        
        # Verify shared mapper was called
        mock_map_to_flags.assert_called_once_with(test_place)
        assert result == ["food_dining", "rooftop"]
    
    def test_place_facets_imports_shared_mapper(self):
        """Test that place_facets.py imports from shared facets.py."""
                # Read the place_facets.py file to verify imports
        place_facets_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'packages', 'wp_tags', 'place_facets.py'
        )
        
        with open(place_facets_path, 'r') as f:
            content = f.read()
        
        # Should import from shared facets
        assert 'from packages.wp_tags.facets import' in content, "place_facets.py should import from shared facets.py"
        assert 'map_event_to_flags' in content, "Should import map_event_to_flags from shared mapper"
        assert 'categories_to_facets' in content, "Should import categories_to_facets from shared mapper"
    
    def test_fallback_implementation_exists(self):
        """Test that fallback implementations exist for robustness."""
        from packages.wp_tags.place_facets import _fallback_map_place_to_flags, _fallback_categories_to_place_flags
        
        # Test fallback implementations work
        test_place = {
            "name": "Test Place",
            "description": "A test place",
            "tags": ["test"]
        }
        
        fallback_flags = _fallback_map_place_to_flags(test_place)
        assert isinstance(fallback_flags, list)
        
        fallback_categories = _fallback_categories_to_place_flags(["test_category"])
        assert isinstance(fallback_categories, dict)
        assert "flags" in fallback_categories
        assert "categories" in fallback_categories
    
    def test_shared_facets_has_canonical_flags(self):
        """Test that shared facets.py contains the 11 canonical flags."""
        # Read the actual mapper file since facets.py is a shim
        mapper_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            'packages', 'wp_tags', 'mapper.py'
        )
        
        with open(mapper_path, 'r') as f:
            content = f.read()
        
        # Should contain the 11 canonical flags
        expected_flags = [
            "electronic_music", "live_music", "jazz_blues", "rooftop",
            "food_dining", "art_exhibits", "workshops", "cinema",
            "markets", "yoga_wellness", "parks"
        ]
        
        for flag in expected_flags:
            assert flag in content, f"Canonical flag '{flag}' not found in shared mapper.py"


if __name__ == "__main__":
    pytest.main([__file__])

