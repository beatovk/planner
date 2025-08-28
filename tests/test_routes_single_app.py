"""
Test that the single FastAPI app contains both events and places routes.
"""

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_app_has_events_routes(client):
    """Test that the app has events-related routes."""
    response = client.get("/api/events")
    # Should not return 404 (route exists)
    assert response.status_code != 404


def test_app_has_places_routes(client):
    """Test that the app has places-related routes."""
    response = client.get("/api/places")
    # Should not return 404 (route exists)
    assert response.status_code != 404


def test_app_has_root_route(client):
    """Test that the app has a root route."""
    response = client.get("/")
    assert response.status_code == 200


def test_app_structure():
    """Test that the app has the expected structure."""
    routes = [route.path for route in app.routes]
    
    # Check for key routes
    assert "/" in routes
    assert "/api/events" in routes
    assert "/api/places" in routes
    
    # Check for health/status routes
    health_routes = [r for r in routes if "health" in r or "status" in r]
    assert len(health_routes) > 0
