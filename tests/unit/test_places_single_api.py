#!/usr/bin/env python3
"""
Test that only one set of /api/places routes exists.
"""

import pytest
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import app from the new location
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'apps', 'api'))
from app_factory import create_app

app = create_app()


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
        
        # Check for specific expected endpoints based on new structure
        expected_endpoints = [
            '/api/places/health',
            '/api/places/search', 
            '/api/places/recommend'
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
        
        # Check specific endpoints and their methods based on new structure
        expected_methods = {
            '/api/places/health': ['GET'],
            '/api/places/search': ['GET'],
            '/api/places/recommend': ['GET']
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
        """Test that no secondary places API is imported in app_factory.py."""
        # Read app_factory.py content
        app_factory_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'apps', 'api', 'app_factory.py')
        
        with open(app_factory_path, 'r') as f:
            content = f.read()
        
        # Should NOT contain imports from src.api.places_api
        assert 'from src.api.places_api import' not in content, "Secondary places API imported in app_factory.py"
        assert 'register_places_routes' not in content, "register_places_routes called in app_factory.py"
    
    def test_places_endpoints_use_core_service(self):
        """Test that places endpoints use PlacesService correctly."""
        # Read the app_factory.py content
        app_factory_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'apps', 'api', 'app_factory.py')
        
        with open(app_factory_path, 'r') as f:
            content = f.read()
        
        # Should use places_router from packages.wp_places.api
        assert 'from packages.wp_places.api import places_router' in content, "places_router not imported from packages.wp_places.api"
        assert 'app.include_router(places_router)' in content, "places_router not included in app"


if __name__ == "__main__":
    pytest.main([__file__])

