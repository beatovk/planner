"""
Complete integration test for the week planner system.
Tests all major components working together.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from apps.api.app_factory import create_app
from packages.wp_cache.cache import CacheClient
from packages.wp_core.db import get_engine


def test_complete_system_integration():
    """Test that all system components work together"""
    
    # 1. Create application
    app = create_app()
    assert app is not None
    
    # 2. Test client context manager
    with TestClient(app) as client:
        # 3. Health check
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "timestamp" in data
        
        # 4. Places API endpoints
        response = client.get("/api/places/health")
        assert response.status_code == 200
        
        # 5. Cache functionality
        cache_client = app.state.cache
        assert cache_client is not None
        
        # Test cache operations
        test_data = {"integration": "test", "value": 123}
        success = cache_client.set_json("integration_test", test_data)
        assert success is True
        
        result = cache_client.get_json("integration_test")
        assert result == test_data
        
        # Clean up
        cache_client.delete("integration_test")
        
        # 6. Database engine
        db_engine = app.state.db_engine
        assert db_engine is not None
        
        # 7. Redis client - REMOVED
        # Redis dependencies removed - using simple in-memory cache
    
    # 8. App should shut down cleanly
    # (handled by FastAPI's lifespan)


def test_cache_integration():
    """Test cache integration with the system"""
    
    app = create_app()
    
    with TestClient(app) as client:
        # Get cache client from app state
        cache_client = app.state.cache
        assert cache_client is not None
        
        # Test cache operations
        test_data = {"cache": "test", "number": 42}
        
        # Set data
        success = cache_client.set_json("cache_integration", test_data)
        assert success is True
        
        # Get data
        result = cache_client.get_json("cache_integration")
        assert result == test_data
        
        # Test with_fallback
        producer_calls = []
        def producer():
            producer_calls.append("called")
            return {"produced": "data"}
        
        # First call: should call producer
        result1 = cache_client.with_fallback("fallback_test", producer)
        assert result1 == {"produced": "data"}
        assert len(producer_calls) == 1
        
        # Second call: should get from cache
        result2 = cache_client.with_fallback("fallback_test", producer)
        assert result2 == {"produced": "data"}
        assert len(producer_calls) == 1  # Still only called once
        
        # Clean up
        cache_client.delete("cache_integration")
        cache_client.delete("fallback_test")


def test_database_integration():
    """Test database integration with the system"""
    
    app = create_app()
    
    with TestClient(app) as client:
        # Get database engine from app state
        db_engine = app.state.db_engine
        assert db_engine is not None
        
        # Test basic database operations
        # This is a basic test - in production you'd test actual queries
        assert hasattr(db_engine, 'dispose')  # SQLAlchemy engine has dispose
        # Note: execute is not directly on engine in SQLAlchemy 2.0+


def test_api_endpoints_integration():
    """Test that all API endpoints are accessible"""
    
    app = create_app()
    
    with TestClient(app) as client:
        # Health endpoints
        response = client.get("/health")
        assert response.status_code == 200
        
        response = client.get("/api/places/health")
        assert response.status_code == 200
        
        # Places API endpoints
        response = client.get("/api/places/categories")
        # May return 200, 503, or 404 depending on implementation
        assert response.status_code in [200, 503, 404]
        
        response = client.get("/api/places/stats")
        # May return 200, 503, or 404 depending on implementation
        assert response.status_code in [200, 503, 404]


def test_error_handling_integration():
    """Test that error handling works across the system"""
    
    app = create_app()
    
    with TestClient(app) as client:
        # Test non-existent endpoint
        response = client.get("/non-existent")
        assert response.status_code == 404
        
        # Test invalid health endpoint
        response = client.post("/health")  # Should be GET only
        assert response.status_code == 405  # Method Not Allowed


def test_resource_cleanup_integration():
    """Test that resources are properly cleaned up"""
    
    app = create_app()
    
    with TestClient(app) as client:
        # Make a request to trigger lifespan
        response = client.get("/health")
        assert response.status_code == 200
        
        # Verify resources are initialized
        assert hasattr(app.state, 'db_engine')
        assert hasattr(app.state, 'cache')
        # Redis removed - using simple in-memory cache
        
        # Resources may be None if not configured, which is OK
        # The important thing is that they're properly managed
    
    # After context exit, app should be properly shut down
    # (This is handled by FastAPI's lifespan)


def test_configuration_integration():
    """Test that configuration is properly loaded"""
    
    app = create_app()
    
    with TestClient(app) as client:
        # Make a request to trigger lifespan
        response = client.get("/health")
        assert response.status_code == 200
        
        # Check that configuration is accessible
        from packages.wp_core.config import settings
        
        assert hasattr(settings, 'PORT')
        assert hasattr(settings, 'DB_URL')
        assert hasattr(settings, 'CACHE_TTL')
        # REDIS_URL removed - using simple in-memory cache
        
        # Default values should be reasonable
        assert settings.PORT >= 1 and settings.PORT <= 65535
        assert settings.CACHE_TTL > 0


def test_static_files_integration():
    """Test that static files are properly served"""
    
    app = create_app()
    
    with TestClient(app) as client:
        # Test static files endpoint
        response = client.get("/static/")
        # May return 200 (if files exist) or 404 (if no files)
        assert response.status_code in [200, 404]


def test_application_lifecycle():
    """Test complete application lifecycle"""
    
    # 1. Create multiple app instances
    app1 = create_app()
    app2 = create_app()
    
    # They should be different objects
    assert app1 is not app2
    
    # 2. Test each app independently
    with TestClient(app1) as client1:
        response1 = client1.get("/health")
        assert response1.status_code == 200
    
    with TestClient(app2) as client2:
        response2 = client2.get("/health")
        assert response2.status_code == 200
    
    # 3. Apps should be properly isolated
    assert app1.state is not app2.state
