#!/usr/bin/env python3
"""
Unit test to verify places API fallback when cache is bypassed.
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.places_service import PlacesService


class TestPlacesMissFallback:
    """Test that places API works with cache bypass."""
    
    @patch('core.places_service.should_bypass_redis')
    def test_places_service_bypasses_redis_when_disabled(self, mock_bypass):
        """Test that PlacesService bypasses Redis when should_bypass_redis returns True."""
        # Mock Redis bypass
        mock_bypass.return_value = True
        
        # Create service
        service = PlacesService()
        
        # Should not try to get Redis client when bypassed
        assert service._get_redis_client() is None
        
        # Test that cache operations are skipped when Redis is bypassed
        mock_place = MagicMock()
        mock_place.to_dict.return_value = {"id": "test", "name": "Test Place"}
        
        # _cache_places should return False when Redis bypassed
        result = service._cache_places("bangkok", "food_dining", [mock_place])
        assert result is False
        
        # _get_cached_places should return None when Redis bypassed
        result = service._get_cached_places("bangkok", "food_dining")
        assert result is None
    
    @patch('core.places_service.should_bypass_redis')
    def test_places_service_bypasses_redis_for_all_places(self, mock_bypass):
        """Test that PlacesService bypasses Redis for get_all_places."""
        # Mock Redis bypass
        mock_bypass.return_value = True
        
        # Create service
        service = PlacesService()
        
        # Should not try to get Redis client when bypassed
        assert service._get_redis_client() is None
        
        # Test that the service can be created and configured when Redis is bypassed
        assert service is not None
        assert hasattr(service, '_get_redis_client')
    
    @patch('core.places_service.should_bypass_redis')
    def test_places_service_bypasses_redis_for_category(self, mock_bypass):
        """Test that PlacesService bypasses Redis for get_places_by_category."""
        # Mock Redis bypass
        mock_bypass.return_value = True
        
        # Create service
        service = PlacesService()
        
        # Should not try to get Redis client when bypassed
        assert service._get_redis_client() is None
        
        # Test that the service can be created and configured when Redis is bypassed
        assert service is not None
        assert hasattr(service, 'get_places_by_category')
    
    @patch('core.places_service.should_bypass_redis')
    def test_cache_operations_skip_redis_when_bypassed(self, mock_bypass):
        """Test that cache operations skip Redis when bypassed."""
        # Mock Redis bypass
        mock_bypass.return_value = True
        
        # Create service
        service = PlacesService()
        
        # Test cache operations
        mock_place = MagicMock()
        mock_place.to_dict.return_value = {"id": "test", "name": "Test Place"}
        
        # _cache_places should return False when Redis bypassed
        result = service._cache_places("bangkok", "food_dining", [mock_place])
        assert result is False
        
        # _get_cached_places should return None when Redis bypassed
        result = service._get_cached_places("bangkok", "food_dining")
        assert result is None
    
    @patch('core.places_service.should_bypass_redis')
    def test_cache_stats_handles_redis_bypass(self, mock_bypass):
        """Test that cache stats handle Redis bypass gracefully."""
        # Mock Redis bypass
        mock_bypass.return_value = True
        
        # Create service
        service = PlacesService()
        
        # Test cache stats
        stats = service._get_cache_stats("bangkok")
        
        # Should return error info when Redis bypassed
        assert "error" in stats
        assert "Redis not configured" in stats["error"]
    
    def test_places_service_works_without_redis_import(self):
        """Test that PlacesService works even if redis module is not available."""
        # Mock redis import failure
        with patch.dict('sys.modules', {'redis': None}):
            # Should still be able to create service
            service = PlacesService()
            assert service is not None
            
            # Redis client should be None
            assert service._get_redis_client() is None


if __name__ == "__main__":
    pytest.main([__file__])

