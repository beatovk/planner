#!/usr/bin/env python3
"""
Unit test to verify Redis bypass functionality.
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from packages.wp_cache.redis_safe import (
    should_bypass_redis,
    get_redis_status,
    get_config,
)


class TestRedisBypass:
    """Test Redis bypass functionality."""

    @patch.dict(os.environ, {"WP_CACHE_DISABLE": "1"})
    def test_cache_disable_bypass(self):
        """Test that WP_CACHE_DISABLE=1 bypasses Redis."""
        # Clear any cached config
        from packages.wp_cache.redis_safe import _config

        _config.reload_from_env()

        assert should_bypass_redis() is True

        status = get_redis_status()
        assert status["cache_disabled"] is True
        assert status["configured"] is False

    @patch.dict(os.environ, {"REDIS_URL": ""})
    def test_no_redis_url_bypass(self):
        """Test that missing REDIS_URL bypasses Redis."""
        # Clear any cached config
        from packages.wp_cache.redis_safe import _config

        _config.reload_from_env()

        assert should_bypass_redis() is True

        status = get_redis_status()
        assert status["redis_url"] is None
        assert status["configured"] is False

    @patch.dict(os.environ, {"REDIS_URL": "redis://127.0.0.1:6379"})
    def test_redis_configured_when_available(self):
        """Test that Redis is configured when URL is available."""
        # Clear any cached config
        from packages.wp_cache.redis_safe import _config

        _config.reload_from_env()

        # Mock redis import
        with patch("packages.wp_cache.redis_safe.redis") as mock_redis:
            mock_redis.__bool__ = lambda: True

            assert should_bypass_redis() is False

            status = get_redis_status()
            assert status["configured"] is True
            assert status["redis_url"] == "redis://127.0.0.1:6379"

    def test_circuit_breaker_bypass(self):
        """Test that circuit breaker bypasses Redis when open."""
        import time
        from packages.wp_cache.redis_safe import (
            get_circuit_breaker,
            should_bypass_redis,
        )

        # Set up environment
        with patch.dict(os.environ, {"REDIS_URL": "redis://127.0.0.1:6379"}):
            # Clear any cached config
            from packages.wp_cache.redis_safe import _config

            _config.reload_from_env()

            # Mock redis import
            with patch("packages.wp_cache.redis_safe.redis") as mock_redis:
                mock_redis.__bool__ = lambda: True

                # Get circuit breaker and force it open
                breaker = get_circuit_breaker("127.0.0.1:6379")
                breaker.state = "OPEN"
                breaker.last_failure_time = (
                    time.time()
                )  # Recent failure time to keep circuit open

                assert should_bypass_redis() is True

                status = get_redis_status()
                assert status["circuit_breaker"]["state"] == "OPEN"

    def test_circuit_breaker_recovery(self):
        """Test that circuit breaker recovers after timeout."""
        from packages.wp_cache.redis_safe import (
            get_circuit_breaker,
            should_bypass_redis,
        )
        import time

        # Set up environment
        with patch.dict(os.environ, {"REDIS_URL": "redis://127.0.0.1:6379"}):
            # Clear any cached config
            from packages.wp_cache.redis_safe import _config

            _config.reload_from_env()

            # Mock redis import
            with patch("packages.wp_cache.redis_safe.redis") as mock_redis:
                mock_redis.__bool__ = lambda: True

                # Get circuit breaker and force it open
                breaker = get_circuit_breaker("127.0.0.1:6379")
                breaker.state = "OPEN"
                breaker.last_failure_time = (
                    time.time() - 100
                )  # Old failure time to allow recovery

                # Circuit should still be open initially
                assert should_bypass_redis() is True

                # Wait for recovery timeout
                breaker.timeout = 0.1  # Short timeout for testing
                time.sleep(0.2)

                # Circuit should recover
                assert should_bypass_redis() is False

                status = get_redis_status()
                assert status["circuit_breaker"]["state"] == "CLOSED"

    def test_environment_variable_priority(self):
        """Test that environment variables take priority over config."""
        # Test with WP_CACHE_DISABLE=1
        with patch.dict(
            os.environ, {"WP_CACHE_DISABLE": "1", "REDIS_URL": "redis://127.0.0.1:6379"}
        ):
            from packages.wp_cache.redis_safe import _config

            _config.reload_from_env()

            assert should_bypass_redis() is True

            status = get_redis_status()
            assert status["cache_disabled"] is True
            assert status["bypass_reason"] == "WP_CACHE_DISABLE=1"

    def test_redis_connection_failure_bypass(self):
        """Test that Redis connection failure triggers bypass."""
        with patch.dict(os.environ, {"REDIS_URL": "redis://invalid:6379"}):
            from packages.wp_cache.redis_safe import _config

            _config.reload_from_env()

            # Mock redis import to fail
            with patch("packages.wp_cache.redis_safe.redis", None):
                assert should_bypass_redis() is True

                status = get_redis_status()
                assert status["configured"] is False
                assert "redis import failed" in status.get("error", "")


if __name__ == "__main__":
    pytest.main([__file__])
