#!/usr/bin/env python
"""
Mock Redis cache for testing without Redis server.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

CACHE_VERSION = "v2"
DEFAULT_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "1800"))  # 30 мин
STALE_TTL_SECONDS = int(os.getenv("CACHE_STALE_TTL_SECONDS", "7200"))  # 2 часа

# In-memory storage for testing
_mock_cache = {}
_mock_ttl = {}


class MockRedis:
    """Mock Redis client for testing."""
    
    def __init__(self):
        self.decode_responses = True
    
    def get(self, key: str) -> Optional[str]:
        """Get value from mock cache."""
        if key in _mock_cache:
            # Check TTL
            if key in _mock_ttl:
                if datetime.now() > _mock_ttl[key]:
                    # Expired, remove
                    del _mock_cache[key]
                    del _mock_ttl[key]
                    return None
            return _mock_cache[key]
        return None
    
    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set value in mock cache."""
        _mock_cache[key] = value
        if ex:
            _mock_ttl[key] = datetime.now() + timedelta(seconds=ex)
        return True
    
    def setex(self, key: str, ex: int, value: str) -> bool:
        """Set value with expiration in mock cache."""
        return self.set(key, value, ex=ex)
    
    def ping(self) -> bool:
        """Mock ping."""
        return True


def _require_redis() -> MockRedis:
    """Return mock Redis for testing."""
    return MockRedis()


def make_flag_key(city: str, day: str, flag: str, *, stale: bool = False) -> str:
    city = city.lower()
    flag = flag.lower()
    prefix = f"{CACHE_VERSION}:{city}:{day}:flag:{flag}"
    return f"{prefix}:stale" if stale else prefix


def make_index_key(city: str, day: str) -> str:
    return f"{CACHE_VERSION}:{city.lower()}:{day}:index"


def read_flag_ids(
    r: MockRedis, city: str, day: str, flag: str
) -> Tuple[List[str], str]:
    """
    Возвращает (ids, status) где status ∈ {"HIT", "STALE", "MISS"}.
    """
    k = make_flag_key(city, day, flag)
    data = r.get(k)
    if data:
        try:
            return json.loads(data), "HIT"
        except Exception:
            pass
    # SWR fallback: stale-ключ
    ks = make_flag_key(city, day, flag, stale=True)
    data = r.get(ks)
    if data:
        try:
            return json.loads(data), "STALE"
        except Exception:
            pass
    return [], "MISS"


def write_flag_ids(
    r: MockRedis,
    city: str,
    day: str,
    flag: str,
    ids: Iterable[str],
    *,
    ttl: int = DEFAULT_TTL_SECONDS,
    stale_ttl: int = STALE_TTL_SECONDS,
) -> None:
    payload = json.dumps(list(ids), separators=(",", ":"))
    k = make_flag_key(city, day, flag)
    ks = make_flag_key(city, day, flag, stale=True)
    # Основной и "stale" ключи
    r.set(k, payload, ex=ttl)
    r.set(ks, payload, ex=stale_ttl)


def update_index(
    r: MockRedis,
    city: str,
    day: str,
    *,
    flag_counts: Dict[str, int],
    ttl: int = DEFAULT_TTL_SECONDS,
) -> None:
    idx_key = make_index_key(city, day)
    now = datetime.now(timezone.utc).isoformat()
    idx = {"flags": flag_counts, "updated_at": now, "ttl": ttl}
    r.set(idx_key, json.dumps(idx, separators=(",", ":")), ex=ttl)


def ping() -> Dict[str, Any]:
    """Быстрая проверка подключения к Redis."""
    return {"ok": True, "url": "mock://localhost:6379"}


def ensure_client() -> MockRedis:
    return _require_redis()


def read_events_by_ids(
    r: MockRedis, city: str, day: str, event_ids: List[str]
) -> List[Dict[str, Any]]:
    """
    Читает события по ID из кэша.
    TODO: В будущем можно добавить batch чтение из Redis
    """
    # Пока возвращаем пустой список, так как события хранятся в БД
    # В будущем можно добавить кэширование самих событий
    return []


def clear_mock_cache():
    """Clear mock cache for testing."""
    global _mock_cache, _mock_ttl
    _mock_cache.clear()
    _mock_ttl.clear()
