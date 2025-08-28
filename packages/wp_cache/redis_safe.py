#!/usr/bin/env python3
"""
Safe Redis integration with circuit breaker pattern and timeout protection.
Prevents Redis operations from blocking the server thread.
"""

import os
import time
import logging
from typing import Optional, Callable, Any
from urllib.parse import urlparse
from contextlib import suppress
from dataclasses import dataclass

try:
    import redis
    from redis import exceptions as rx
except ImportError:
    redis = None
    rx = None

logger = logging.getLogger(__name__)


def _env(name: str, default: str) -> str:
    v = os.getenv(name)
    return default if v is None or v == "" else v


@dataclass
class _RedisConfig:
    bypass: bool = False
    socket_timeout: float = 2.5
    connect_timeout: float = 2.0
    read_timeout: float = 2.5
    write_timeout: float = 2.5
    ping_timeout: float = 1.0
    retry_on_timeout: bool = True
    pool_max_connections: int = 16
    circuit_breaker_threshold: int = 3
    circuit_breaker_window_sec: int = 60
    recovery_cooldown_sec: int = 30
    redis_url: Optional[str] = None
    connect_timeout_ms: int = 300
    op_timeout_ms: int = 500
    circuit_open_sec: int = 60
    cache_disable: bool = False

    def is_configured(self) -> bool:
        """Check if Redis is configured and enabled."""
        return bool(self.redis_url) and not self.cache_disable and redis is not None

    def get_host_port(self) -> Optional[str]:
        """Extract host:port from REDIS_URL for circuit breaker keying."""
        if not self.redis_url:
            return None
        try:
            parsed = urlparse(self.redis_url)
            return f"{parsed.hostname}:{parsed.port or 6379}"
        except Exception:
            return "unknown:6379"

    def reload_from_env(self):
        """Reload configuration from environment variables (for tests)."""
        global _circuit_breakers
        self.bypass = _env("REDIS_BYPASS", "0") == "1"
        self.socket_timeout = float(_env("REDIS_SOCKET_TIMEOUT", "2.5"))
        self.connect_timeout = float(_env("REDIS_CONNECT_TIMEOUT", "2.0"))
        self.read_timeout = float(_env("REDIS_READ_TIMEOUT", "2.5"))
        self.write_timeout = float(_env("REDIS_WRITE_TIMEOUT", "2.5"))
        self.ping_timeout = float(_env("REDIS_PING_TIMEOUT", "1.0"))
        self.retry_on_timeout = _env("REDIS_RETRY_ON_TIMEOUT", "1") == "1"
        self.pool_max_connections = int(_env("REDIS_POOL_MAX_CONNECTIONS", "16"))
        self.circuit_breaker_threshold = int(_env("REDIS_CB_THRESHOLD", "3"))
        self.circuit_breaker_window_sec = int(_env("REDIS_CB_WINDOW_SEC", "60"))
        self.recovery_cooldown_sec = int(_env("REDIS_CB_RECOVERY_SEC", "30"))
        self.redis_url = _env("REDIS_URL", "") or None
        self.connect_timeout_ms = int(_env("REDIS_CONNECT_TIMEOUT_MS", "300"))
        self.op_timeout_ms = int(_env("REDIS_OP_TIMEOUT_MS", "500"))
        self.circuit_open_sec = int(_env("REDIS_CIRCUIT_OPEN_SEC", "60"))
        self.cache_disable = _env("WP_CACHE_DISABLE", "0") == "1"
        # Clear circuit breakers when reloading config
        _circuit_breakers.clear()


# Defaults with env overrides
_config = _RedisConfig(
    bypass=_env("REDIS_BYPASS", "0") == "1",
    socket_timeout=float(_env("REDIS_SOCKET_TIMEOUT", "2.5")),
    connect_timeout=float(_env("REDIS_CONNECT_TIMEOUT", "2.0")),
    read_timeout=float(_env("REDIS_READ_TIMEOUT", "2.5")),
    write_timeout=float(_env("REDIS_WRITE_TIMEOUT", "2.5")),
    ping_timeout=float(_env("REDIS_PING_TIMEOUT", "1.0")),
    retry_on_timeout=_env("REDIS_RETRY_ON_TIMEOUT", "1") == "1",
    pool_max_connections=int(_env("REDIS_POOL_MAX_CONNECTIONS", "16")),
    circuit_breaker_threshold=int(_env("REDIS_CB_THRESHOLD", "3")),
    circuit_breaker_window_sec=int(_env("REDIS_CB_WINDOW_SEC", "60")),
    recovery_cooldown_sec=int(_env("REDIS_CB_RECOVERY_SEC", "30")),
    redis_url=_env("REDIS_URL", "") or None,
    connect_timeout_ms=int(_env("REDIS_CONNECT_TIMEOUT_MS", "300")),
    op_timeout_ms=int(_env("REDIS_OP_TIMEOUT_MS", "500")),
    circuit_open_sec=int(_env("REDIS_CIRCUIT_OPEN_SEC", "60")),
    cache_disable=_env("WP_CACHE_DISABLE", "0") == "1",
)


def get_config() -> _RedisConfig:
    return _config


def should_bypass_redis() -> bool:
    return _config.bypass


# convenience for tests
def set_bypass_for_tests(flag: bool) -> None:
    _config.bypass = bool(flag)


def should_bypass_redis() -> bool:
    """Check if Redis should be bypassed globally."""
    if _config.bypass:
        return True

    if not _config.redis_url:
        return True

    host_port = _config.get_host_port()
    if host_port:
        breaker = get_circuit_breaker(host_port)
        return breaker.should_bypass()

    return False


def reset_config():
    """Reset config to default values from environment."""
    global _config, _circuit_breakers
    _config.reload_from_env()


class CircuitBreaker:
    """Process-local circuit breaker for Redis operations."""

    def __init__(self, host_port: str, open_window_sec: int = 60):
        self.host_port = host_port
        self.open_window_sec = open_window_sec
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def should_bypass(self) -> bool:
        """Check if circuit is open and should bypass Redis."""
        if self.state == "OPEN":
            if self.last_failure_time is None:
                return True  # Bypass Redis if no failure time recorded
            if time.time() - self.last_failure_time > self.open_window_sec:
                self.state = "HALF_OPEN"
                logger.info(f"Circuit breaker {self.host_port} moved to HALF_OPEN")
            else:
                return True  # Bypass Redis
        return False

    def record_success(self):
        """Record successful operation."""
        self.failure_count = 0
        if self.state != "CLOSED":
            self.state = "CLOSED"
            logger.info(f"Circuit breaker {self.host_port} moved to CLOSED")

    def record_failure(self):
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= 2 and self.state == "CLOSED":
            self.state = "OPEN"
            logger.warning(
                f"Circuit breaker {self.host_port} opened after {self.failure_count} failures"
            )
        elif self.state == "HALF_OPEN":
            self.state = "OPEN"
            logger.warning(
                f"Circuit breaker {self.host_port} reopened after HALF_OPEN failure"
            )


# Global configuration and circuit breakers
_circuit_breakers: dict[str, CircuitBreaker] = {}
_sync_client = None


def get_config():
    """Get Redis configuration."""
    return _config


def get_circuit_breaker(host_port: str) -> CircuitBreaker:
    """Get or create circuit breaker for host:port."""
    if host_port not in _circuit_breakers:
        _circuit_breakers[host_port] = CircuitBreaker(
            host_port, _config.circuit_open_sec
        )
    return _circuit_breakers[host_port]


def get_sync_client() -> Optional["redis.Redis"]:
    """Get Redis sync client with timeouts, no eager connect."""
    global _sync_client

    if not _config.is_configured():
        return None

    if _sync_client is None:
        try:
            _sync_client = redis.from_url(
                _config.redis_url,
                decode_responses=True,
                socket_connect_timeout=_config.connect_timeout_ms / 1000.0,
                socket_timeout=_config.op_timeout_ms / 1000.0,
                retry_on_timeout=_config.retry_on_timeout,
                health_check_interval=30,
            )
            logger.debug("Redis sync client created with timeouts")
        except Exception as e:
            logger.error(f"Failed to create Redis client: {e}")
            return None

    return _sync_client


def get_async_client():
    """Get Redis async client (placeholder for future async support)."""
    # TODO: Implement when async routes are added
    logger.warning("Async Redis client not yet implemented")
    return None


def safe_call(
    fn: Callable[[], Any], *, op_timeout_ms: int, breaker: CircuitBreaker, on_fail=None
):
    """
    Execute fn() with Redis operation timeouts.
    If Redis errors occur, opens circuit and returns on_fail.
    Never blocks the caller.
    """
    if breaker.should_bypass():
        return on_fail

    try:
        val = fn()
        breaker.record_success()
        return val
    except (rx.TimeoutError, rx.ConnectionError, rx.BusyLoadingError, OSError) as e:
        logger.warning(f"Redis operation failed: {e}")
        breaker.record_failure()
        return on_fail
    except Exception as e:
        logger.error(f"Unexpected Redis error: {e}")
        breaker.record_failure()
        return on_fail


def get_redis_status() -> dict:
    """Get Redis status for diagnostics."""
    config = get_config()
    host_port = config.get_host_port()

    status = {
        "configured": config.is_configured(),
        "cache_disabled": config.cache_disable,
        "redis_url": config.redis_url,
        "timeouts": {
            "connect_ms": config.connect_timeout_ms,
            "op_ms": config.op_timeout_ms,
        },
    }

    if host_port and host_port in _circuit_breakers:
        breaker = _circuit_breakers[host_port]
        status["circuit_breaker"] = {
            "state": breaker.state,
            "host_port": host_port,
            "failure_count": breaker.failure_count,
            "last_failure": breaker.last_failure_time,
        }

    return status
