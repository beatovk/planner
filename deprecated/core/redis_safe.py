import warnings
warnings.warn("core.redis_safe is deprecated; use packages.wp_cache.redis_safe", DeprecationWarning)

from packages.wp_cache.redis_safe import (
    _RedisConfig, _config, get_config, should_bypass_redis,
    CircuitBreaker, get_circuit_breaker, get_redis_status,
    set_bypass_for_tests, reset_config,
)  # noqa

# Re-export redis module for tests that need to patch it
try:
    from packages.wp_cache.redis_safe import redis
except ImportError:
    redis = None
