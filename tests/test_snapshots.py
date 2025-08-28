from __future__ import annotations

import gzip
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from unittest import mock

import fakeredis
import pytest

from core.models import Event
from ingest.scheduler import run_ingest_once
from storage.snapshots import should_snapshot, build_snapshot_path, save_snapshot
from storage.db import Database


def test_should_snapshot_top_percent():
    assert should_snapshot(10, 0, top_percent=0.2) is True  # 2 items -> idx 0,1
    assert should_snapshot(10, 1, top_percent=0.2) is True
    assert should_snapshot(10, 2, top_percent=0.2) is False
    assert should_snapshot(0, 0, top_percent=0.2) is False


def test_build_snapshot_path_rel():
    dt = datetime(2024, 1, 11, 10, 0, tzinfo=timezone.utc)
    rel = build_snapshot_path("abc", dt, "/base")
    assert rel.endswith("2024/01/11/abc.html.gz")


def test_save_snapshot_writes_gz(tmp_path: Path, monkeypatch):
    target = tmp_path / "2024/01/11/e1.html.gz"
    html = "<html>OK</html>"

    class Resp:
        status_code = 200
        text = html

        def raise_for_status(self):
            return None

    monkeypatch.setattr("requests.get", lambda *a, **k: Resp())
    save_snapshot("http://example.com/x", str(target))
    assert target.exists()
    with gzip.open(target, "rt", encoding="utf-8") as f:
        assert f.read() == html


def test_ingest_integration_sets_raw_html_ref(tmp_path: Path, monkeypatch):
    # ENV
    db_url = f"sqlite:///{tmp_path/'wp.db'}"
    os.environ["DB_URL"] = db_url
    os.environ["CITY"] = "bangkok"
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    os.environ["SNAPSHOT_ENABLE"] = "true"
    os.environ["SNAPSHOT_TOP_PERCENT"] = (
        "0.5"  # из 2 событий делаем снапшот только для первого
    )
    os.environ["SNAPSHOT_DIR"] = str(tmp_path / "snaps")

    # Fake redis
    import storage.cache as cache_mod

    r = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(cache_mod, "get_redis", lambda url=None: r)

    # Fake collect_events
    import core.aggregator as agg

    def _dt(y, m, d):
        return datetime(y, m, d, 12, 0, tzinfo=timezone.utc)

    evs: List[Event] = [
        Event(
            id="e1",
            title="A",
            url="https://a",
            source="timeout_bkk",
            start=_dt(2024, 1, 11),
            end=_dt(2024, 1, 11),
            categories=["food"],
        ),
        Event(
            id="e2",
            title="B",
            url="https://b",
            source="bk_magazine",
            start=_dt(2024, 1, 12),
            end=_dt(2024, 1, 12),
            categories=["nightlife"],
        ),
    ]
    monkeypatch.setattr(agg, "collect_events", lambda: evs)

    # Mock network
    class Resp:
        status_code = 200
        text = "<html>hi</html>"

        def raise_for_status(self):
            return None

    monkeypatch.setattr("requests.get", lambda *a, **k: Resp())

    # Run
    run_ingest_once(days_ahead=1)

    # e1 должен получить raw_html_ref и на диске должен быть .gz
    db = Database(db_url)
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, raw_html_ref FROM events ORDER BY id"
        ).fetchall()
        row_map = {r[0]: r[1] for r in rows}
        assert row_map["e1"] is not None and row_map["e2"] in (None, "")
        gz_path = Path(os.environ["SNAPSHOT_DIR"]) / row_map["e1"]
        assert gz_path.exists()
