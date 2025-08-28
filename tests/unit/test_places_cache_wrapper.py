#!/usr/bin/env python3
"""
Unit test to verify PlacesService uses shared cache from core/cache.py.
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from packages.wp_places.service import PlacesService


class TestPlacesServiceCacheWrapper:
    """Test that PlacesService uses shared cache from core/cache.py."""

    @patch("core.places_service.is_configured")
    @patch("core.places_service.ensure_client")
    def test_places_service_uses_shared_cache(
        self, mock_ensure_client, mock_is_configured
    ):
        """Test that PlacesService calls shared cache functions."""
        # Setup mocks
        mock_is_configured.return_value = True
        mock_client = MagicMock()
        mock_ensure_client.return_value = mock_client

        # Create service
        service = PlacesService()

        # Test cache key generation
        cache_key = service._get_place_cache_key("bangkok", "food_dining")
        assert cache_key == "v1:places:bangkok:flag:food_dining"

        stale_key = service._get_place_stale_key("bangkok", "food_dining")
        assert stale_key == "v1:places:bangkok:flag:food_dining:stale"

        index_key = service._get_place_index_key("bangkok")
        assert index_key == "v1:places:bangkok:index"

        # Verify shared cache functions were called
        mock_is_configured.assert_called_once()
        mock_ensure_client.assert_called_once()

    @patch("core.places_service.is_configured")
    @patch("core.places_service.ensure_client")
    def test_cache_places_calls_shared_cache(
        self, mock_ensure_client, mock_is_configured
    ):
        """Test that _cache_places uses shared Redis client."""
        # Setup mocks
        mock_is_configured.return_value = True
        mock_client = MagicMock()
        mock_ensure_client.return_value = mock_client

        # Create service
        service = PlacesService()

        # Mock Place objects
        mock_place = MagicMock()
        mock_place.to_dict.return_value = {
            "id": "test1",
            "name": "Test Place",
            "city": "bangkok",
            "flags": ["food_dining"],
        }

        # Test caching
        result = service._cache_places("bangkok", "food_dining", [mock_place], 3600)

        # Verify Redis operations
        assert result is True
        mock_client.setex.assert_called_once()
        mock_client.sadd.assert_called_once()
        mock_client.expire.assert_called_once()

    @patch("core.places_service.is_configured")
    @patch("core.places_service.ensure_client")
    def test_get_cached_places_calls_shared_cache(
        self, mock_ensure_client, mock_is_configured
    ):
        """Test that _get_cached_places uses shared Redis client."""
        # Setup mocks
        mock_is_configured.return_value = True
        mock_client = MagicMock()
        mock_ensure_client.return_value = mock_client

        # Mock cached data
        mock_client.get.return_value = '[{"id": "test1", "name": "Test Place"}]'

        # Create service
        service = PlacesService()

        # Test getting cached places
        with patch("core.places_service.Place.from_dict") as mock_from_dict:
            mock_place = MagicMock()
            mock_from_dict.return_value = mock_place

            result = service._get_cached_places("bangkok", "food_dining")

            # Verify Redis operations
            assert mock_client.get.call_count >= 1  # At least one call for hot cache
            mock_from_dict.assert_called_once()

    @patch("core.places_service.is_configured")
    def test_cache_disabled_when_redis_not_configured(self, mock_is_configured):
        """Test that cache operations fail gracefully when Redis is not configured."""
        # Setup mock
        mock_is_configured.return_value = False

        # Create service
        service = PlacesService()

        # Test cache operations return False when Redis not configured
        result = service._cache_places("bangkok", "food_dining", [], 3600)
        assert result is False

        cached_places = service._get_cached_places("bangkok", "food_dining")
        assert cached_places is None

    def test_cache_key_format_matches_v1_spec(self):
        """Test that cache keys follow v1:places format specification."""
        service = PlacesService()

        # Test key formats
        assert (
            service._get_place_cache_key("bangkok", "food_dining")
            == "v1:places:bangkok:flag:food_dining"
        )
        assert (
            service._get_place_cache_key("chiang_mai", "art_exhibits")
            == "v1:places:chiang_mai:flag:art_exhibits"
        )
        assert (
            service._get_place_stale_key("bangkok", "rooftop")
            == "v1:places:bangkok:flag:rooftop:stale"
        )
        assert service._get_place_index_key("bangkok") == "v1:places:bangkok:index"


if __name__ == "__main__":
    pytest.main([__file__])
