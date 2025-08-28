from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from core.models import Event
from storage.db import Database


def _dt(y, m, d):
    return datetime(y, m, d, 12, 0, tzinfo=timezone.utc)


def test_db_create_and_upsert_and_get(tmp_path: Path):
    db_file = tmp_path / "wp.db"
    db = Database(f"sqlite:///{db_file}")
    db.create_tables()

    # create two events, second is a duplicate id (should upsert)
    e1 = Event(
        id="e-1",
        title="Street Food Market",
        url="https://timeout.example/sfm",
        source="timeout_bkk",
        start=_dt(2024, 1, 11),
        end=_dt(2024, 1, 11),
        categories=["food"],
        tags=["streetfood"],
        attrs={"streetfood": True},
    )
    e1b = Event(
        id="e-1",  # same id -> upsert
        title="Street Food Market (updated)",
        url="https://timeout.example/sfm",
        source="timeout_bkk",
        start=_dt(2024, 1, 11),
        end=_dt(2024, 1, 11),
        categories=["food"],
        tags=["streetfood"],
        attrs={"streetfood": True, "market": True},
    )
    e2 = Event(
        id="e-2",
        title="Rooftop Jazz Night",
        url="https://bk.example/rjn",
        source="bk_magazine",
        start=_dt(2024, 1, 11),
        end=_dt(2024, 1, 11),
        categories=["nightlife"],
        tags=["music", "rooftop"],
        attrs={"rooftop": True},
    )

    # first insert
    wrote = db.upsert_events([e1, e2], city="bangkok")
    assert wrote == 2

    # upsert duplicate (same id) + one new -> still idempotent on count per id
    wrote2 = db.upsert_events([e1b], city="bangkok")
    assert wrote2 == 1

    # query by date
    ids_all = db.get_events_by_date(city="bangkok", day_iso="2024-01-11")
    assert set(ids_all) == {"e-1", "e-2"}

    # filter by category
    ids_food = db.get_events_by_date(
        city="bangkok", day_iso="2024-01-11", category="food"
    )
    assert ids_food == ["e-1"]

    # filter by flag
    ids_rooftop = db.get_events_by_date(
        city="bangkok", day_iso="2024-01-11", flag="rooftop"
    )
    assert ids_rooftop == ["e-2"]

    # ensure only 2 rows in DB
    with sqlite3.connect(str(db_file)) as conn:
        cur = conn.execute("SELECT COUNT(*) FROM events")
        (cnt,) = cur.fetchone()
        assert cnt == 2
