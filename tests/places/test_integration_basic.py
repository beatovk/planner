"""
Integration tests for places: save → search → cache.
"""

import pytest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock
import sys

# Add project root to path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from packages.wp_places.service import PlacesService
from packages.wp_places.dao import init_schema, save_places
from packages.wp_core.db import get_engine
from packages.wp_models.place import Place


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    # Create engine for temp database
    engine = get_engine()

    yield engine

    # Cleanup
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def sample_places():
    """Sample places data for testing."""
    return [
        {
            "id": "test_place_1",
            "name": "Test Restaurant",
            "description": "A test restaurant for integration testing",
            "city": "bangkok",
            "address": "123 Test Street",
            "tags": ["restaurant", "food", "test"],
            "flags": ["food_dining", "test"],
            "typical_time": "2 hours",
            "source": "test",
            "rating": 4.5,
            "price_range": "$$",
            "google_maps_url": "https://maps.google.com/test1",
        },
        {
            "id": "test_place_2",
            "name": "Test Cafe",
            "description": "A test cafe for integration testing",
            "city": "bangkok",
            "address": "456 Test Avenue",
            "tags": ["cafe", "coffee", "test"],
            "flags": ["cafes", "test"],
            "typical_time": "1 hour",
            "source": "test",
            "rating": 4.0,
            "price_range": "$",
            "google_maps_url": "https://maps.google.com/test2",
        },
    ]


@pytest.fixture
def places_service():
    """Create PlacesService instance for testing."""
    return PlacesService()


def test_save_places_to_database(temp_db, sample_places):
    """Test saving places to database."""
    # Initialize schema
    init_schema(temp_db)

    # Save places
    result = save_places(temp_db, sample_places)

    assert result == len(sample_places)
    assert result == 2


def test_search_places_after_save(temp_db, sample_places):
    """Test searching places after saving them."""
    # Initialize schema and save places
    init_schema(temp_db)
    save_places(temp_db, sample_places)

    # Create service and search
    service = PlacesService()

    # Search for restaurant
    results = service.search_places("restaurant", limit=10)

    assert len(results) >= 1
    assert any("restaurant" in place.name.lower() for place in results)


def test_cache_integration(temp_db, sample_places):
    """Test that places are cached after search."""
    # Initialize schema and save places
    init_schema(temp_db)
    save_places(temp_db, sample_places)

    # Create service
    service = PlacesService()

    # Mock cache client
    with patch.object(service, "_cache_client") as mock_cache:
        mock_cache.get_json.return_value = None  # Cache miss
        mock_cache.set_json.return_value = True  # Cache set success

        # Perform search (should cache results)
        results = service.search_places("cafe", limit=10)

        # Verify cache was used
        assert mock_cache.get_json.called
        assert mock_cache.set_json.called


def test_search_by_category_integration(temp_db, sample_places):
    """Test search by category integration."""
    # Initialize schema and save places
    init_schema(temp_db)
    save_places(temp_db, sample_places)

    # Create service
    service = PlacesService()

    # Search by food category
    results = service.search_places("food", category="food_dining", limit=10)

    assert len(results) >= 1
    assert any("food_dining" in place.flags for place in results)


def test_cache_key_generation():
    """Test that cache keys are generated correctly."""
    service = PlacesService()

    # Test different cache key patterns
    city = "bangkok"
    flag = "food_dining"
    query = "restaurant"

    # Flag-based key
    flag_key = service._get_place_cache_key(city, flag)
    assert "v2:places:bangkok:flag:food_dining" in flag_key

    # Search-based key
    search_key = service._get_search_cache_key(city, query, 20)
    assert "v2:places:bangkok:search:restaurant:20" in search_key


def test_cache_ttl_configuration():
    """Test that cache TTL is configured correctly."""
    from packages.wp_core.config import get_cache_ttl

    # Test different TTL types
    default_ttl = get_cache_ttl("default")
    long_ttl = get_cache_ttl("long")
    short_ttl = get_cache_ttl("short")

    assert default_ttl > 0
    assert long_ttl > default_ttl
    assert short_ttl < default_ttl


def test_database_health_check(temp_db):
    """Test database health check functionality."""
    from packages.wp_core.db import healthcheck

    # Health check should pass for valid database
    result = healthcheck()
    assert result is True


def test_cache_bypass_configuration():
    """Test cache bypass configuration."""
    from packages.wp_core.config import is_cache_enabled

    # Test with different environment configurations
    with patch.dict(os.environ, {"CACHE_BYPASS": "1"}):
        from packages.wp_core.config import Settings

        test_settings = Settings()
        assert test_settings.CACHE_BYPASS is True

    with patch.dict(os.environ, {"WP_CACHE_DISABLE": "1"}):
        from packages.wp_core.config import Settings

        test_settings = Settings()
        assert test_settings.WP_CACHE_DISABLE is True


def test_full_workflow_integration(temp_db, sample_places):
    """Test complete workflow: save → search → cache → retrieve."""
    # Initialize schema
    init_schema(temp_db)

    # Save places
    save_result = save_places(temp_db, sample_places)
    assert save_result == 2

    # Create service
    service = PlacesService()

    # Mock cache for controlled testing
    with patch.object(service, "_cache_client") as mock_cache:
        # First search (cache miss)
        mock_cache.get_json.return_value = None
        mock_cache.set_json.return_value = True

        results1 = service.search_places("test", limit=10)
        assert len(results1) >= 2

        # Verify cache was set
        assert mock_cache.set_json.called

        # Second search (cache hit)
        mock_cache.get_json.return_value = [place.to_dict() for place in results1]

        results2 = service.search_places("test", limit=10)
        assert len(results2) >= 2

        # Verify cache was used
        assert mock_cache.get_json.called
