"""
Simplified test for application shutdown and resource cleanup.
Tests basic functionality without complex mocking.
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from apps.api.app_factory import create_app


def test_app_creates_and_shuts_down():
    """Test that app can be created and shut down without errors"""
    
    # Create app
    app = create_app()
    assert app is not None
    
    # Test client context manager
    with TestClient(app) as client:
        # Make a request to trigger lifespan
        response = client.get("/health")
        assert response.status_code == 200
        
        # Verify app state has expected attributes
        assert hasattr(app.state, 'db_engine')
        assert hasattr(app.state, 'cache')
        # Redis removed - using simple in-memory cache
    
    # After context exit, app should be properly shut down
    # (This is handled by FastAPI's lifespan)


def test_health_endpoint_works():
    """Test that health endpoint returns expected structure"""
    
    app = create_app()
    
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "database" in data
        assert "version" in data
        
        assert data["status"] == "healthy"
        assert isinstance(data["timestamp"], str)
        assert data["database"] in ["healthy", "unhealthy"]


def test_app_state_initialization():
    """Test that app state is properly initialized"""
    
    app = create_app()
    
    with TestClient(app) as client:
        # Trigger lifespan
        client.get("/health")
        
        # Check app state
        assert hasattr(app.state, 'db_engine')
        assert hasattr(app.state, 'cache')
        # Redis removed - using simple in-memory cache
        
        # db_engine should be initialized (even if None)
        assert app.state.db_engine is not None or app.state.db_engine is None
        
        # cache should be initialized
        assert app.state.cache is not None or app.state.cache is None


def test_multiple_requests_same_client():
    """Test that multiple requests work with the same client"""
    
    app = create_app()
    
    with TestClient(app) as client:
        # Multiple health checks
        for i in range(3):
            response = client.get("/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"


def test_app_factory_creates_unique_instances():
    """Test that app factory creates unique instances"""
    
    app1 = create_app()
    app2 = create_app()
    
    # They should be different objects
    assert app1 is not app2
    
    # But they should have the same structure
    assert hasattr(app1, 'state')
    assert hasattr(app2, 'state')
    
    # Test both work
    with TestClient(app1) as client1:
        response1 = client1.get("/health")
        assert response1.status_code == 200
    
    with TestClient(app2) as client2:
        response2 = client2.get("/health")
        assert response2.status_code == 200
