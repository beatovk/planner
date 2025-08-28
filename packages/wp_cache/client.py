"""
Redis client factory for the week planner application.
Provides a simple way to create Redis clients with proper configuration.
"""

import asyncio
from typing import Optional, Union
from packages.wp_core.config import settings

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None

try:
    import redis
    REDIS_SYNC_AVAILABLE = True
except ImportError:
    REDIS_SYNC_AVAILABLE = False
    redis = None


async def build_redis(url: str) -> Optional[Union["aioredis.Redis", "redis.Redis"]]:
    """
    Build Redis client from URL string.
    
    Args:
        url: Redis connection URL
        
    Returns:
        Redis client instance or None if Redis is not available
    """
    if not REDIS_AVAILABLE:
        print("Warning: aioredis not available, Redis async client cannot be created")
        return None
    
    try:
        # Parse Redis URL
        if url.startswith("redis://"):
            # Extract host, port, db from URL
            parts = url.replace("redis://", "").split("/")
            if len(parts) > 1:
                host_port = parts[0].split(":")
                host = host_port[0] if host_port[0] else "localhost"
                port = int(host_port[1]) if len(host_port) > 1 and host_port[1] else 6379
                db = int(parts[1]) if parts[1].isdigit() else 0
            else:
                host = "localhost"
                port = 6379
                db = 0
            
            # Create async Redis client
            client = aioredis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,
                socket_connect_timeout=settings.REDIS_TIMEOUT,
                socket_timeout=settings.REDIS_TIMEOUT,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await client.ping()
            print(f"✅ Redis connected: {host}:{port}/{db}")
            return client
            
        else:
            print(f"Warning: Unsupported Redis URL format: {url}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to create Redis client: {e}")
        return None


def build_sync_redis(url: str) -> Optional["redis.Redis"]:
    """
    Build synchronous Redis client from URL string.
    
    Args:
        url: Redis connection URL
        
    Returns:
        Redis client instance or None if Redis is not available
    """
    if not REDIS_SYNC_AVAILABLE:
        print("Warning: redis not available, Redis sync client cannot be created")
        return None
    
    try:
        # Parse Redis URL
        if url.startswith("redis://"):
            # Extract host, port, db from URL
            parts = url.replace("redis://", "").split("/")
            if len(parts) > 1:
                host_port = parts[0].split(":")
                host = host_port[0] if host_port[0] else "localhost"
                port = int(host_port[1]) if len(host_port) > 1 and host_port[1] else 6379
                db = int(parts[1]) if parts[1].isdigit() else 0
            else:
                host = "localhost"
                port = 6379
                db = 0
            
            # Create sync Redis client
            client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,
                socket_connect_timeout=settings.REDIS_TIMEOUT,
                socket_timeout=settings.REDIS_TIMEOUT,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            client.ping()
            print(f"✅ Redis sync connected: {host}:{port}/{db}")
            return client
            
        else:
            print(f"Warning: Unsupported Redis URL format: {url}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to create Redis sync client: {e}")
        return None
