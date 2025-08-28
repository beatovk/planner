"""
Test health endpoint functionality.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from apps.api.app_factory import create_app

@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)

def test_health_endpoint_returns_200(client):
    """Test that GET /health returns 200 status."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"

def test_health_endpoint_structure(client):
    """Test that health endpoint returns expected structure."""
    response = client.get("/health")
    data = response.json()
    
    # Check required fields
    required_fields = ["status", "timestamp"]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"
    
    # Check status value
    assert data["status"] == "healthy"
    
    # Check timestamp format (should be ISO string)
    assert isinstance(data["timestamp"], str)
    assert "T" in data["timestamp"]  # ISO format indicator

def test_health_endpoint_pings_database(client):
    """Test that health endpoint pings database."""
    with patch('packages.wp_core.db.healthcheck') as mock_healthcheck:
        mock_healthcheck.return_value = True
        
        response = client.get("/health")
        assert response.status_code == 200
        
        # Verify database health check was called
        mock_healthcheck.assert_called_once()

def test_health_endpoint_handles_database_failure(client):
    """Test that health endpoint handles database failure gracefully."""
    with patch('packages.wp_core.db.healthcheck') as mock_healthcheck:
        mock_healthcheck.side_effect = Exception("Database connection failed")
        
        response = client.get("/health")
        assert response.status_code == 200  # Should still return 200
        
        data = response.json()
        assert data["status"] == "healthy"  # Should still show healthy

def test_health_endpoint_caching(client):
    """Test that health endpoint responses are not cached."""
    # First request
    response1 = client.get("/health")
    data1 = response1.json()
    
    # Second request
    response2 = client.get("/health")
    data2 = response2.json()
    
    # Timestamps should be different (no caching)
    assert data1["timestamp"] != data2["timestamp"]
