from __future__ import annotations

import time
from typing import List

import fakeredis

from storage.cache import (
    cache_get_candidates,
    cache_set_candidates,
    key_for_category,
    key_for_flag,
)


def test_key_helpers():
    assert key_for_category("Bangkok", "2024-01-11", "Food") == "bangkok:2024-01-11:food"
    assert key_for_flag("Bangkok", "2024-01-11", "Outdoor") == "bangkok:2024-01-11:flag:outdoor"


def test_set_and_get_fresh():
    r = fakeredis.FakeRedis(decode_responses=True)
    key = "bkk:2024-01-11:food"
    ids = ["e1", "e2", "e3"]
    cache_set_candidates(r, key, ids, ttl_s=20, swr_margin_s=60)
    got, stale = cache_get_candidates(r, key, ttl_s=20, swr_margin_s=60)
    assert got == ids  # order preserved
    assert stale is False


def test_swr_window_and_expiry():
    r = fakeredis.FakeRedis(decode_responses=True)
    key = "bkk:2024-01-11:flag:outdoor"
    ids = ["a", "b"]
    # ttl=1s, swr=2s -> total redis TTL=3s
    cache_set_candidates(r, key, ids, ttl_s=1, swr_margin_s=2)
    # Immediately fresh
    got, stale = cache_get_candidates(r, key, ttl_s=1, swr_margin_s=2)
    assert got == ids and stale is False
    # After > ttl but < ttl+swr -> stale but served
    time.sleep(1.2)
    got2, stale2 = cache_get_candidates(r, key, ttl_s=1, swr_margin_s=2)
    assert got2 == ids and stale2 is True
    # After > ttl+swr -> key expired
    time.sleep(2.2)
    got3, stale3 = cache_get_candidates(r, key, ttl_s=1, swr_margin_s=2)
    assert got3 is None and stale3 is True


def test_corrupted_payload_treated_as_miss():
    r = fakeredis.FakeRedis(decode_responses=True)
    key = "bkk:2024-01-11:nightlife"
    r.set(key, "{not-json")
    got, stale = cache_get_candidates(r, key, ttl_s=10, swr_margin_s=60)
    assert got is None and stale is True
