#!/usr/bin/env python3
"""
Unit test to verify circuit breaker functionality.
"""

import pytest
import sys
import os
import time
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from packages.wp_cache.redis_safe import CircuitBreaker, get_circuit_breaker


class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    def test_circuit_breaker_initial_state(self):
        """Test that circuit breaker starts in CLOSED state."""
        breaker = CircuitBreaker("127.0.0.1:6379")
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 0
        assert breaker.last_failure_time is None
        assert breaker.should_bypass() is False
    
    def test_circuit_breaker_opens_after_failures(self):
        """Test that circuit breaker opens after 2 consecutive failures."""
        breaker = CircuitBreaker("127.0.0.1:6379")
        
        # First failure
        breaker.record_failure()
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 1
        
        # Second failure - should open
        breaker.record_failure()
        assert breaker.state == "OPEN"
        assert breaker.failure_count == 2
        assert breaker.should_bypass() is True
    
    def test_circuit_breaker_resets_on_success(self):
        """Test that circuit breaker resets to CLOSED on success."""
        breaker = CircuitBreaker("127.0.0.1:6379")
        
        # Open the circuit
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == "OPEN"
        
        # Record success - should close
        breaker.record_success()
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 0
    
    def test_circuit_breaker_half_open_transition(self):
        """Test that circuit breaker moves to HALF_OPEN after timeout."""
        breaker = CircuitBreaker("127.0.0.1:6379", open_window_sec=1)
        
        # Open the circuit
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == "OPEN"
        
        # Wait for timeout
        time.sleep(1.1)
        
        # Should move to HALF_OPEN
        assert breaker.should_bypass() is False
        assert breaker.state == "HALF_OPEN"
    
    def test_circuit_breaker_reopens_on_half_open_failure(self):
        """Test that circuit breaker reopens on HALF_OPEN failure."""
        breaker = CircuitBreaker("127.0.0.1:6379", open_window_sec=1)
        
        # Open the circuit
        breaker.record_failure()
        breaker.record_failure()
        
        # Wait for timeout and move to HALF_OPEN
        time.sleep(1.1)
        breaker.should_bypass()  # This moves to HALF_OPEN
        
        # Record failure in HALF_OPEN - should reopen
        breaker.record_failure()
        assert breaker.state == "OPEN"
        assert breaker.should_bypass() is True
    
    def test_circuit_breaker_closes_on_half_open_success(self):
        """Test that circuit breaker closes on HALF_OPEN success."""
        breaker = CircuitBreaker("127.0.0.1:6379", open_window_sec=1)
        
        # Open the circuit
        breaker.record_failure()
        breaker.record_failure()
        
        # Wait for timeout and move to HALF_OPEN
        time.sleep(1.1)
        breaker.should_bypass()  # This moves to HALF_OPEN
        
        # Record success in HALF_OPEN - should close
        breaker.record_success()
        assert breaker.state == "CLOSED"
        assert breaker.should_bypass() is False
    
    def test_circuit_breaker_host_port_keying(self):
        """Test that circuit breakers are keyed by host:port."""
        breaker1 = get_circuit_breaker("127.0.0.1:6379")
        breaker2 = get_circuit_breaker("127.0.0.1:6379")
        breaker3 = get_circuit_breaker("redis-cloud.com:14374")
        
        # Same host:port should return same breaker
        assert breaker1 is breaker2
        
        # Different host:port should return different breaker
        assert breaker1 is not breaker3
        
        # Test state isolation
        breaker1.state = "OPEN"
        assert breaker2.state == "OPEN"  # Same instance
        assert breaker3.state == "CLOSED"  # Different instance
    
    def test_circuit_breaker_timeout_configuration(self):
        """Test circuit breaker timeout configuration."""
        # Test default timeout
        breaker = CircuitBreaker("127.0.0.1:6379")
        assert breaker.open_window_sec == 60
        
        # Test custom timeout
        breaker = CircuitBreaker("127.0.0.1:6379", open_window_sec=30)
        assert breaker.open_window_sec == 30


if __name__ == "__main__":
    pytest.main([__file__])

