"""
Test cache policy and TTL behavior.
Ensures that cache bypass, TTL, and hit/miss behavior work correctly.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from packages.wp_cache.cache import CacheClient
from packages.wp_core.config import settings


@pytest.fixture
def mock_redis_client():
    """Mock Redis client"""
    mock_client = Mock()
    mock_client.get = Mock()
    mock_client.set = Mock()
    mock_client.delete = Mock()
    mock_client.exists = Mock()
    mock_client.ttl = Mock()
    return mock_client


@pytest.fixture
def cache_client(mock_redis_client):
    """Cache client with mocked Redis"""
    with patch('packages.wp_cache.redis_safe.get_sync_client', return_value=mock_redis_client), \
         patch('packages.wp_cache.redis_safe.should_bypass_redis', return_value=False):
        return CacheClient(default_ttl=3600)


@pytest.fixture
def cache_client_bypass():
    """Cache client with bypass enabled"""
    with patch('packages.wp_cache.redis_safe.should_bypass_redis', return_value=True):
        return CacheClient(default_ttl=3600)


def test_cache_bypass_disabled_normal_behavior(cache_client, mock_redis_client):
    """Test normal cache behavior when bypass is disabled"""
    
    # Mock Redis responses
    mock_redis_client.get.return_value = None  # Cache miss
    mock_redis_client.set.return_value = True
    
    # Test cache miss -> set
    result = cache_client.get_json("test_key")
    assert result is None
    
    # Set value
    test_data = {"name": "test", "value": 123}
    success = cache_client.set_json("test_key", test_data)
    assert success is True
    
    # Verify Redis was called
    mock_redis_client.set.assert_called_once()
    mock_redis_client.get.assert_called_once()


def test_cache_bypass_enabled_always_miss(cache_client_bypass):
    """Test that cache bypass always results in cache miss"""
    
    # Even if we try to set, it should be bypassed
    test_data = {"name": "test", "value": 123}
    success = cache_client_bypass.set_json("test_key", test_data)
    assert success is False  # Bypassed
    
    # Get should always return None
    result = cache_client_bypass.get_json("test_key")
    assert result is None


def test_cache_ttl_respects_default(cache_client, mock_redis_client):
    """Test that cache respects default TTL"""
    
    test_data = {"name": "test", "value": 123}
    
    # Set with default TTL
    cache_client.set_json("test_key", test_data)
    
    # Verify Redis set was called with default TTL
    mock_redis_client.set.assert_called_once()
    call_args = mock_redis_client.set.call_args
    
    # Check that TTL was passed (should be 3600 from fixture)
    assert len(call_args[0]) >= 3  # key, value, ttl
    assert call_args[0][2] == 3600  # default TTL


def test_cache_ttl_custom_override(cache_client, mock_redis_client):
    """Test that custom TTL overrides default"""
    
    test_data = {"name": "test", "value": 123}
    custom_ttl = 1800  # 30 minutes
    
    # Set with custom TTL
    cache_client.set_json("test_key", test_data, ttl=custom_ttl)
    
    # Verify Redis set was called with custom TTL
    mock_redis_client.set.assert_called_once()
    call_args = mock_redis_client.set.call_args
    
    # Check that custom TTL was used
    assert len(call_args[0]) >= 3
    assert call_args[0][2] == custom_ttl


def test_cache_hit_miss_flow(cache_client, mock_redis_client):
    """Test complete cache hit/miss flow"""
    
    test_data = {"name": "test", "value": 123}
    
    # First: cache miss
    mock_redis_client.get.return_value = None
    result = cache_client.get_json("test_key")
    assert result is None
    
    # Set the value
    mock_redis_client.set.return_value = True
    success = cache_client.set_json("test_key", test_data)
    assert success is True
    
    # Second: cache hit
    mock_redis_client.get.return_value = '{"name": "test", "value": 123}'
    result = cache_client.get_json("test_key")
    assert result == test_data
    
    # Verify Redis calls
    assert mock_redis_client.get.call_count == 2
    assert mock_redis_client.set.call_count == 1


def test_cache_with_fallback_producer_called_once(cache_client, mock_redis_client):
    """Test that with_fallback calls producer only once on cache miss"""
    
    # Mock cache miss
    mock_redis_client.get.return_value = None
    mock_redis_client.set.return_value = True
    
    # Producer function that should be called only once
    producer_calls = []
    def producer():
        producer_calls.append("called")
        return {"data": "produced"}
    
    # First call: cache miss, producer called
    result1 = cache_client.with_fallback("test_key", producer)
    assert result1 == {"data": "produced"}
    assert len(producer_calls) == 1
    
    # Second call: cache hit, producer not called
    mock_redis_client.get.return_value = '{"data": "produced"}'
    result2 = cache_client.with_fallback("test_key", producer)
    assert result2 == {"data": "produced"}
    assert len(producer_calls) == 1  # Still only called once


def test_cache_with_fallback_producer_called_on_every_miss(cache_client, mock_redis_client):
    """Test that producer is called on every cache miss"""
    
    # Mock cache miss every time
    mock_redis_client.get.return_value = None
    mock_redis_client.set.return_value = True
    
    producer_calls = []
    def producer():
        producer_calls.append("called")
        return {"data": f"produced_{len(producer_calls)}"}
    
    # Multiple calls with cache miss
    for i in range(3):
        result = cache_client.with_fallback("test_key", producer)
        assert result == {"data": f"produced_{i+1}"}
    
    # Producer should be called 3 times
    assert len(producer_calls) == 3


def test_cache_ttl_validation(cache_client, mock_redis_client):
    """Test TTL validation and edge cases"""
    
    test_data = {"name": "test", "value": 123}
    
    # Test zero TTL (should use default)
    cache_client.set_json("test_key", test_data, ttl=0)
    call_args = mock_redis_client.set.call_args
    assert call_args[0][2] == 3600  # default TTL
    
    # Test negative TTL (should use default)
    cache_client.set_json("test_key", test_data, ttl=-1)
    call_args = mock_redis_client.set.call_args
    assert call_args[0][2] == 3600  # default TTL
    
    # Test very large TTL
    large_ttl = 86400 * 365  # 1 year
    cache_client.set_json("test_key", test_data, ttl=large_ttl)
    call_args = mock_redis_client.set.call_args
    assert call_args[0][2] == large_ttl


def test_cache_error_handling(cache_client, mock_redis_client):
    """Test that cache handles Redis errors gracefully"""
    
    # Mock Redis errors
    mock_redis_client.get.side_effect = Exception("Redis connection failed")
    mock_redis_client.set.side_effect = Exception("Redis write failed")
    
    # Get should return None on error
    result = cache_client.get_json("test_key")
    assert result is None
    
    # Set should return False on error
    success = cache_client.set_json("test_key", {"data": "test"})
    assert success is False


def test_cache_bypass_environment_variable():
    """Test that cache bypass respects environment variable"""
    
    # Test with bypass enabled
    with patch.dict(os.environ, {'WP_CACHE_DISABLE': '1'}):
        with patch('packages.wp_cache.redis_safe.should_bypass_redis', return_value=True):
            client = CacheClient()
            assert client._cache_bypass is True
    
    # Test with bypass disabled
    with patch.dict(os.environ, {'WP_CACHE_DISABLE': '0'}):
        with patch('packages.wp_cache.redis_safe.should_bypass_redis', return_value=False):
            client = CacheClient()
            assert client._cache_bypass is False


def test_cache_ttl_from_config():
    """Test that cache TTL is read from config"""
    
    # Mock config settings
    with patch('packages.wp_core.config.settings') as mock_settings:
        mock_settings.CACHE_TTL = 7200  # 2 hours
        
        with patch('packages.wp_cache.redis_safe.should_bypass_redis', return_value=True):
            client = CacheClient()
            assert client.default_ttl == 7200


def test_cache_key_patterns(cache_client, mock_redis_client):
    """Test that cache uses consistent key patterns"""
    
    test_data = {"name": "test"}
    mock_redis_client.set.return_value = True
    
    # Test different key patterns
    keys = [
        "simple_key",
        "key:with:colons",
        "key.with.dots",
        "key-with-dashes",
        "key with spaces",
        "key123"
    ]
    
    for key in keys:
        cache_client.set_json(key, test_data)
        mock_redis_client.set.assert_called()
        # Verify key was passed as-is
        assert mock_redis_client.set.call_args[0][0] == key


def test_cache_json_serialization(cache_client, mock_redis_client):
    """Test that cache properly serializes/deserializes JSON"""
    
    # Complex data structure
    test_data = {
        "string": "hello",
        "number": 42,
        "boolean": True,
        "null": None,
        "list": [1, 2, 3],
        "dict": {"nested": "value"},
        "unicode": "привет мир"
    }
    
    # Mock Redis responses
    mock_redis_client.get.return_value = None  # First call: miss
    mock_redis_client.set.return_value = True
    
    # Set data
    success = cache_client.set_json("test_key", test_data)
    assert success is True
    
    # Mock Redis to return the serialized data
    import json
    serialized = json.dumps(test_data)
    mock_redis_client.get.return_value = serialized
    
    # Get data
    result = cache_client.get_json("test_key")
    assert result == test_data
