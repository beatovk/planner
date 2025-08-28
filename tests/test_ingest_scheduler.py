from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List

import fakeredis
import pytest

from core.models import Event
from ingest.scheduler import _group_ids_by_category_and_flags, run_ingest_once
from storage.cache import cache_get_candidates
from storage.db import Database


def _dt(y, m, d):
    return datetime(y, m, d, 12, 0, tzinfo=timezone.utc)


def test_grouping_into_cache_keys():
    today = datetime.now(timezone.utc).date().isoformat()
    evs: List[Event] = [
        Event(id="e1", title="Street Food", url="https://a", source="timeout_bkk",
              start=_dt(2024, 1, 11), end=_dt(2024, 1, 11),
              categories=["food"], attrs={"streetfood": True}),
        Event(id="e2", title="Rooftop Night", url="https://b", source="bk_magazine",
              start=_dt(2024, 1, 11), end=_dt(2024, 1, 11),
              categories=["nightlife"], attrs={"rooftop": True}),
    ]
    keys = _group_ids_by_category_and_flags(evs, city="bangkok", days=[_dt(2024,1,11)])
    assert "bangkok:2024-01-11:food" in keys and keys["bangkok:2024-01-11:food"] == ["e1"]
    assert "bangkok:2024-01-11:flag:streetfood" in keys
    assert "bangkok:2024-01-11:flag:rooftop" in keys


def test_run_ingest_once_writes_db_and_cache(tmp_path: Path, monkeypatch):
    # Prepare env
    db_url = f"sqlite:///{tmp_path/'wp.db'}"
    os.environ["DB_URL"] = db_url
    os.environ["CITY"] = "bangkok"
    os.environ["CACHE_TTL_S"] = "60"
    os.environ["CACHE_SWR_MARGIN_S"] = "30"

    # Fake redis
    r = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    # Patch get_redis to return fake
    import storage.cache as cache_mod
    monkeypatch.setattr(cache_mod, "get_redis", lambda url=None: r)

    # Patch collect_events to return fixed events
    import core.aggregator as agg
    evs: List[Event] = [
        Event(id="e1", title="Street Food", url="https://a", source="timeout_bkk",
              start=_dt(2024, 1, 11), end=_dt(2024, 1, 11),
              categories=["food"], attrs={"streetfood": True}),
        Event(id="e2", title="Rooftop Night", url="https://b", source="bk_magazine",
              start=_dt(2024, 1, 12), end=_dt(2024, 1, 12),
              categories=["nightlife"], attrs={"rooftop": True}),
    ]
    monkeypatch.setattr(agg, "collect_events", lambda: evs)

    # Run
    run_ingest_once(days_ahead=1)

    # DB rows = 2
    db = Database(db_url)
    with db.connect() as conn:
        (cnt,) = conn.execute("SELECT COUNT(*) FROM events").fetchone()
        assert cnt == 2

    # Cache keys exist for two days
    got_food_day1, _ = cache_get_candidates(
        r, "bangkok:2024-01-11:food", ttl_s=60, swr_margin_s=30
    )
    got_roof_day2, _ = cache_get_candidates(
        r, "bangkok:2024-01-12:flag:rooftop", ttl_s=60, swr_margin_s=30
    )
    assert got_food_day1 == ["e1"]
    assert got_roof_day2 == ["e2"]
