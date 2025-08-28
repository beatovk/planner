"""
Test cache hit flow: consecutive calls should show MISS → HIT.
"""

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_cache_hit_flow_places(client):
    """Test that consecutive places API calls show cache MISS → HIT flow."""
    # First call - should be MISS
    response1 = client.get("/api/places?city=bangkok&flags=markets&limit=3")
    assert response1.status_code == 200

    # Check cache status header
    cache_status1 = response1.headers.get("x-cache-status", "UNKNOWN")
    print(f"First call cache status: {cache_status1}")

    # Second call - should be HIT if Redis is configured
    response2 = client.get("/api/places?city=bangkok&flags=markets&limit=3")
    assert response2.status_code == 200

    cache_status2 = response2.headers.get("x-cache-status", "UNKNOWN")
    print(f"Second call cache status: {cache_status2}")

    # If Redis is configured, second call should be HIT
    # If Redis is not configured, both should be BYPASS
    if cache_status1 == "MISS":
        assert cache_status2 in [
            "HIT",
            "STALE",
        ], f"Expected HIT/STALE, got {cache_status2}"
    elif cache_status1 == "BYPASS":
        assert cache_status2 == "BYPASS", f"Expected BYPASS, got {cache_status2}"


def test_cache_headers_present(client):
    """Test that cache-related headers are present."""
    response = client.get("/api/places?city=bangkok&flags=markets&limit=3")
    assert response.status_code == 200

    # Check for cache headers
    headers = response.headers
    assert "x-cache-status" in headers
    assert "x-source" in headers

    # Cache status should be one of the expected values
    cache_status = headers["x-cache-status"]
    assert cache_status in [
        "HIT",
        "MISS",
        "STALE",
        "BYPASS",
    ], f"Unexpected cache status: {cache_status}"

    # Source should be one of the expected values
    source = headers["x-source"]
    assert source in ["cache", "db", "fetcher"], f"Unexpected source: {source}"


def test_redis_circuit_breaker_header(client):
    """Test that Redis circuit breaker status is reported in headers."""
    response = client.get("/api/places?city=bangkok&flags=markets&limit=3")
    assert response.status_code == 200

    # Check for Redis circuit breaker header
    if "x-redis-circuit" in response.headers:
        circuit_status = response.headers["x-redis-circuit"]
        assert circuit_status in [
            "CLOSED",
            "OPEN",
            "HALF_OPEN",
        ], f"Unexpected circuit status: {circuit_status}"
