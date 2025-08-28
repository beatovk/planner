#!/usr/bin/env python3
"""
Unit test to verify single places API (no duplicate endpoints).
"""

import pytest
import sys
import os
from fastapi import FastAPI

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from main import app


class TestPlacesSingleAPI:
    """Test that only one set of /api/places routes exists."""
    
    def test_places_endpoints_exist_in_main_app(self):
        """Test that places endpoints exist in the main app."""
        # Get all routes from the main app
        routes = app.routes
        
        # Find places-related routes
        places_routes = []
        for route in routes:
            if hasattr(route, 'path') and route.path and '/api/places' in route.path:
                places_routes.append(route.path)
        
        # Should have places endpoints
        assert len(places_routes) > 0, "No /api/places endpoints found in main app"
        
        # Check for specific expected endpoints
        expected_endpoints = [
            '/api/places',
            '/api/places/categories', 
            '/api/places/stats',
            '/api/places/warm-cache'
        ]
        
        for endpoint in expected_endpoints:
            assert any(route.path == endpoint for route in routes), f"Missing endpoint: {endpoint}"
    
    def test_no_duplicate_places_endpoints(self):
        """Test that there are no duplicate /api/places endpoints."""
        routes = app.routes
        
        # Count occurrences of each places endpoint
        endpoint_counts = {}
        for route in routes:
            if hasattr(route, 'path') and route.path and '/api/places' in route.path:
                path = route.path
                endpoint_counts[path] = endpoint_counts.get(path, 0) + 1
        
        # Check for duplicates
        duplicates = {path: count for path, count in endpoint_counts.items() if count > 1}
        assert len(duplicates) == 0, f"Duplicate endpoints found: {duplicates}"
    
    def test_places_endpoints_have_correct_methods(self):
        """Test that places endpoints have the correct HTTP methods."""
        routes = app.routes
        
        # Check specific endpoints and their methods
        expected_methods = {
            '/api/places': ['GET'],
            '/api/places/categories': ['GET'],
            '/api/places/stats': ['GET'],
            '/api/places/warm-cache': ['POST']
        }
        
        for endpoint, expected_methods_list in expected_methods.items():
            route = next((r for r in routes if hasattr(r, 'path') and r.path == endpoint), None)
            assert route is not None, f"Endpoint not found: {endpoint}"
            
            # Check if route has the expected methods
            if hasattr(route, 'methods'):
                route_methods = list(route.methods)
                for method in expected_methods_list:
                    assert method in route_methods, f"Method {method} not found for {endpoint}"
    
    def test_no_secondary_places_api_imported(self):
        """Test that no secondary places API is imported in main.py."""
        # Read main.py content
        main_py_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'main.py')
        
        with open(main_py_path, 'r') as f:
            content = f.read()
        
        # Should NOT contain imports from src.api.places_api
        assert 'from src.api.places_api import' not in content, "Secondary places API imported in main.py"
        assert 'register_places_routes' not in content, "register_places_routes called in main.py"
    
    def test_places_endpoints_use_core_service(self):
        """Test that places endpoints use PlacesService correctly."""
        # Read the actual main.py content since main.py is a shim
        main_py_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'apps', 'api', 'main.py')
        
        with open(main_py_path, 'r') as f:
            content = f.read()
        
        # Should use PlacesService from packages.wp_places.service
        assert 'from packages.wp_places.service import PlacesService' in content, "PlacesService not imported from packages.wp_places.service"
        assert 'PlacesService()' in content, "PlacesService not instantiated in endpoints"


if __name__ == "__main__":
    pytest.main([__file__])

