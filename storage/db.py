from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from packages.wp_models.event import Event


def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


@dataclass
class Database:
    """Lightweight DB wrapper (SQLite for MVP, Postgres: TODO)."""

    url: str  # e.g., "sqlite:///data.db"

    def _is_sqlite(self) -> bool:
        return self.url.startswith("sqlite:///")

    def _sqlite_path(self) -> Path:
        return Path(self.url[len("sqlite:///") :])

    def connect(self) -> sqlite3.Connection:
        if self._is_sqlite():
            path = self._sqlite_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(path))
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA foreign_keys=ON")
            return conn
        raise NotImplementedError("Only sqlite is supported in MVP. Use sqlite:///...")

    def create_tables(self) -> None:
        with self.connect() as conn:
            cur = conn.cursor()
            # events: JSON stored as TEXT; datetimes as ISO strings
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    desc TEXT,
                    start TEXT,
                    end TEXT,
                    time_str TEXT,
                    venue TEXT,
                    area TEXT,
                    address TEXT,
                    image TEXT,
                    url TEXT NOT NULL,
                    price_min REAL,
                    categories TEXT,   -- JSON array
                    tags TEXT,         -- JSON array
                    attrs TEXT,        -- JSON object
                    source TEXT NOT NULL,
                    fetched_at TEXT NOT NULL,
                    raw_html_ref TEXT,
                    city TEXT NOT NULL DEFAULT 'bangkok'
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS event_sources (
                    source TEXT PRIMARY KEY,
                    last_seen TEXT,
                    meta TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS ingest_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    source TEXT NOT NULL,
                    count INTEGER NOT NULL,
                    ok INTEGER NOT NULL,
                    note TEXT
                )
                """
            )
            # optional: snapshots registry (file storage handled elsewhere)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    event_id TEXT PRIMARY KEY,
                    path TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            # indexes (expression index on date portion of ISO datetime)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_city_startdate "
                "ON events (city, substr(start,1,10))"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_source ON events (source)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_fetched_at ON events (fetched_at)"
            )
            conn.commit()

    def upsert_events(self, events: List[Event], *, city: str = "bangkok") -> int:
        """Idempotent batch upsert by Event.id."""
        if not events:
            return 0
        rows = []
        for e in events:
            rows.append(
                (
                    e.id,
                    e.title,
                    e.desc,
                    _iso(e.start),
                    _iso(e.end),
                    e.time_str,
                    e.venue,
                    e.area,
                    e.address,
                    str(e.image) if e.image else None,
                    str(e.url),
                    e.price_min,
                    json.dumps(e.categories or []),
                    json.dumps(e.tags or []),
                    json.dumps(e.attrs or {}),
                    e.source,
                    _iso(e.fetched_at),
                    e.raw_html_ref,
                    city,
                )
            )
        sql = """
            INSERT INTO events (
                id, title, desc, start, end, time_str, venue, area, address, image,
                url, price_min, categories, tags, attrs, source, fetched_at, raw_html_ref, city
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                desc=excluded.desc,
                start=excluded.start,
                end=excluded.end,
                time_str=excluded.time_str,
                venue=excluded.venue,
                area=excluded.area,
                address=excluded.address,
                image=excluded.image,
                url=excluded.url,
                price_min=excluded.price_min,
                categories=excluded.categories,
                tags=excluded.tags,
                attrs=excluded.attrs,
                source=excluded.source,
                fetched_at=CASE
                    WHEN excluded.fetched_at > events.fetched_at THEN excluded.fetched_at
                    ELSE events.fetched_at
                END,
                raw_html_ref=excluded.raw_html_ref,
                city=excluded.city
        """
        with self.connect() as conn:
            cur = conn.cursor()
            cur.executemany(sql, rows)
            conn.commit()
        return len(rows)

    def get_events_by_date(
        self,
        *,
        city: str,
        day_iso: str,  # "YYYY-MM-DD"
        category: Optional[str] = None,
        flag: Optional[str] = None,
    ) -> List[str]:
        """Return event IDs for a given city & day, with optional category/flag filter.
        Filtering by category/flag is done in Python to avoid JSON1 dependency.
        """
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, categories, tags, attrs FROM events "
                "WHERE city=? AND substr(start,1,10)=?",
                (city, day_iso),
            )
            out: List[str] = []
            for _id, cats_j, tags_j, attrs_j in cur.fetchall():
                cats = []
                tags = []
                attrs = {}
                try:
                    cats = json.loads(cats_j) if cats_j else []
                    tags = json.loads(tags_j) if tags_j else []
                    attrs = json.loads(attrs_j) if attrs_j else {}
                except Exception:
                    pass
                if category and category.lower() not in [c.lower() for c in cats]:
                    continue
                if flag and not bool(attrs.get(flag, False)):
                    continue
                out.append(_id)
            return out

    def record_ingest(self, *, source: str, count: int, ok: bool, note: Optional[str] = None) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO ingest_log (ts, source, count, ok, note) VALUES (?, ?, ?, ?, ?)",
                (datetime.utcnow().isoformat(), source, count, 1 if ok else 0, note),
            )
            conn.commit()
