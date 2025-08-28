from __future__ import annotations

import json
import os
import time
from typing import List, Optional, Tuple

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # will be injected in tests via fakeredis


def get_redis(url: Optional[str] = None):
    """
    Create a Redis client (decode_responses=True).
    Uses REDIS_URL if url is None.
    """
    url = url or os.environ.get("REDIS_URL")
    if not url:
        raise RuntimeError("REDIS_URL is not set")
    if redis is None:
        raise RuntimeError("redis package not available")
    return redis.Redis.from_url(url, decode_responses=True)


def key_for_category(city: str, day_iso: str, category: str) -> str:
    """city:day:category"""
    return f"{city.lower()}:{day_iso}:{category.lower()}"


def key_for_flag(city: str, day_iso: str, flag: str) -> str:
    """city:day:flag:<flagname>"""
    return f"{city.lower()}:{day_iso}:flag:{flag.lower()}"


def _payload(ids: List[str]) -> str:
    # store ts + ttl so we can compute staleness precisely
    return json.dumps(
        {
            "ids": [str(i) for i in ids],
            "ts": int(time.time()),
        }
    )


def cache_set_candidates(
    r,
    key: str,
    ids: List[str],
    ttl_s: int,
    *,
    swr_margin_s: int = 300,
) -> None:
    """
    Set candidates with TTL and SWR extension.
    We store JSON payload with creation ts.
    The Redis key TTL is set to ttl_s + swr_margin_s to allow serving
    stale-but-valid data inside the SWR window.
    """
    ttl_total = max(1, int(ttl_s) + int(swr_margin_s))
    r.setex(key, ttl_total, _payload(ids))


def cache_get_candidates(
    r,
    key: str,
    *,
    ttl_s: int,
    swr_margin_s: int = 300,
) -> Tuple[Optional[List[str]], bool]:
    """
    Get candidates with SWR semantics.
    Returns (ids | None, is_stale).
    - If key missing (expired beyond SWR): (None, True)
    - If present and age > ttl_s: (ids, True)  -> serve stale, trigger revalidate
    - If present and age <= ttl_s: (ids, False)
    """
    raw = r.get(key)
    if raw is None:
        return None, True
    try:
        obj = json.loads(raw)
        ids = [str(x) for x in (obj.get("ids") or [])]
        ts = int(obj.get("ts") or 0)
    except Exception:  # corrupted payload -> treat as miss
        return None, True

    age = max(0, int(time.time()) - ts)
    is_stale = age > int(ttl_s)
    return ids, is_stale
