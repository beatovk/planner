"""
Test application shutdown and resource cleanup.
Ensures that resources are properly disposed when the application shuts down.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from apps.api.app_factory import create_app


@pytest.fixture
def mock_redis():
    """Mock Redis client with connection pool"""
    mock_client = Mock()
    mock_pool = Mock()
    mock_client.connection_pool = mock_pool
    mock_client.close = Mock()
    mock_pool.disconnect = Mock()
    return mock_client


@pytest.fixture
def mock_engine():
    """Mock database engine"""
    mock_engine = Mock()
    mock_engine.dispose = Mock()
    return mock_engine


def test_lifespan_cleanup_redis_available(mock_redis, mock_engine):
    """Test that Redis resources are properly closed when Redis is available"""
    
    with patch('packages.wp_core.config.settings') as mock_settings, \
         patch('packages.wp_cache.client.build_redis', return_value=mock_redis) as mock_build_redis, \
         patch('packages.wp_core.db.get_engine', return_value=mock_engine) as mock_get_engine, \
         patch('packages.wp_cache.cache.CacheClient', return_value=Mock()) as mock_cache_client:
        
        # Setup mocks
        mock_settings.REDIS_URL = "redis://localhost:6379/0"  # Enable Redis
        
        # Create app and test client
        app = create_app()
        
        with TestClient(app) as client:
            # Make a request to trigger lifespan startup
            response = client.get("/health")
            assert response.status_code == 200
            
            # Verify Redis was initialized
            mock_build_redis.assert_called_once()
        
        # After exiting context, verify cleanup
        mock_redis.close.assert_called_once()
        mock_redis.connection_pool.disconnect.assert_called_once()
        mock_engine.dispose.assert_called_once()


def test_lifespan_cleanup_redis_unavailable(mock_engine):
    """Test that resources are cleaned up even when Redis is unavailable"""
    
    with patch('packages.wp_core.config.settings') as mock_settings, \
         patch('packages.wp_cache.client.build_redis', return_value=None) as mock_build_redis, \
         patch('packages.wp_core.db.get_engine', return_value=mock_engine) as mock_get_engine, \
         patch('packages.wp_cache.cache.CacheClient', return_value=Mock()) as mock_cache_client:
        
        # Setup mocks - Redis unavailable
        mock_settings.REDIS_URL = None  # Disable Redis
        
        # Create app and test client
        app = create_app()
        
        with TestClient(app) as client:
            # Make a request to trigger lifespan startup
            response = client.get("/health")
            assert response.status_code == 200
            
            # Verify Redis was attempted but failed
            mock_build_redis.assert_called_once()
        
        # After exiting context, verify cleanup
        mock_engine.dispose.assert_called_once()


def test_lifespan_cleanup_cache_client(mock_redis, mock_engine):
    """Test that CacheClient is properly closed if it has a close method"""
    
    mock_cache = Mock()
    mock_cache.close = Mock()
    
    with patch('packages.wp_core.config.settings') as mock_settings, \
         patch('packages.wp_cache.client.build_redis', return_value=mock_redis) as mock_build_redis, \
         patch('packages.wp_core.db.get_engine', return_value=mock_engine) as mock_get_engine, \
         patch('packages.wp_cache.cache.CacheClient', return_value=mock_cache) as mock_cache_class:
        
        # Setup mocks
        mock_settings.REDIS_URL = "redis://localhost:6379/0"  # Enable Redis
        
        # Create app and test client
        app = create_app()
        
        with TestClient(app) as client:
            # Make a request to trigger lifespan startup
            response = client.get("/health")
            assert response.status_code == 200
        
        # After exiting context, verify cache cleanup
        mock_cache.close.assert_called_once()


def test_lifespan_cleanup_graceful_failure_handling(mock_redis, mock_engine):
    """Test that cleanup continues even if individual cleanup steps fail"""
    
    # Make Redis cleanup fail
    mock_redis.close.side_effect = Exception("Redis close failed")
    mock_redis.connection_pool.disconnect.side_effect = Exception("Pool disconnect failed")
    
    # Make engine cleanup fail
    mock_engine.dispose.side_effect = Exception("Engine dispose failed")
    
    with patch('packages.wp_core.config.settings') as mock_settings, \
         patch('packages.wp_cache.client.build_redis', return_value=mock_redis) as mock_build_redis, \
         patch('packages.wp_core.db.get_engine', return_value=mock_engine) as mock_get_engine, \
         patch('packages.wp_cache.cache.CacheClient', return_value=Mock()) as mock_cache_client:
        
        # Setup mocks
        mock_settings.REDIS_URL = "redis://localhost:6379/0"  # Enable Redis
        
        # Create app and test client
        app = create_app()
        
        with TestClient(app) as client:
            # Make a request to trigger lifespan startup
            response = client.get("/health")
            assert response.status_code == 200
        
        # After exiting context, verify cleanup was attempted
        mock_redis.close.assert_called_once()
        mock_redis.connection_pool.disconnect.assert_called_once()
        mock_engine.dispose.assert_called_once()
        
        # App should still shut down gracefully despite cleanup errors


def test_lifespan_initialization_order():
    """Test that resources are initialized in the correct order"""
    
    init_order = []
    
    def mock_build_redis(*args, **kwargs):
        init_order.append("redis")
        return Mock()
    
    def mock_get_engine(*args, **kwargs):
        init_order.append("engine")
        return Mock()
    
    def mock_cache_client(*args, **kwargs):
        init_order.append("cache")
        return Mock()
    
    with patch('packages.wp_core.config.settings') as mock_settings, \
         patch('packages.wp_cache.client.build_redis', side_effect=mock_build_redis), \
         patch('packages.wp_core.db.get_engine', side_effect=mock_get_engine), \
         patch('packages.wp_cache.cache.CacheClient', side_effect=mock_cache_client):
        
        # Enable Redis for this test
        mock_settings.REDIS_URL = "redis://localhost:6379/0"
        
        # Create app and test client
        app = create_app()
        
        with TestClient(app) as client:
            # Make a request to trigger lifespan startup
            response = client.get("/health")
            assert response.status_code == 200
        
        # Verify initialization order: engine -> redis -> cache
        assert init_order == ["engine", "redis", "cache"]
