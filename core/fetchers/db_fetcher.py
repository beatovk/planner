#!/usr/bin/env python
from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import json
import pytz

from .interface import FetcherInterface
from .validator import ensure_events
from ..events import Event
from ..logging import logger
from ..db import get_engine, healthcheck


class DatabaseFetcher(FetcherInterface):
    """Fetcher that reads events from the database instead of scraping."""
    
    name = "db_fetcher"
    SOURCE = "db_fetcher"
    
    def __init__(self, db_url: Optional[str] = None):
        # Используем новый модуль БД с fallback
        self.engine = get_engine()
        print(f"DatabaseFetcher initialized with engine: {self.engine.url}")
    
    def fetch(self, category: Optional[str] = None, limit: Optional[int] = None) -> List[Event]:
        """Fetch events from the database."""
        try:
            raw_events = self._get_events_from_db(category=category, limit=limit)
            return ensure_events(raw_events, source_name=self.SOURCE)
        except Exception as exc:
            logger.warning("db_fetcher fetch failed: %s", exc)
            return []
    
    def _get_events_from_db(self, category: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get events from the database."""
        try:
            # Строим SQL запрос с поддержкой facets
            query = """
                SELECT id, title, desc, start, end, time_str, venue, area, address, 
                       image, url, price_min, categories, tags, attrs, source, 
                       fetched_at, raw_html_ref, city
                FROM events
                WHERE source IN ('timeout_bkk', 'test')
            """
            params = []
            
            # Фильтр по категории
            if category:
                query += " AND (categories LIKE ? OR tags LIKE ?)"
                params.extend([f"%{category}%", f"%{category}%"])
            
            query += " ORDER BY start ASC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            # Выполняем запрос через SQLAlchemy
            print(f"Executing query: {query}")
            print(f"With params: {params}")
            
            try:
                with self.engine.connect() as conn:
                    from sqlalchemy import text
                    result = conn.execute(text(query), params)
                    rows = result.fetchall()
                    print(f"Raw result: {result}")
                    print(f"Query returned {len(rows)} rows")
                    if rows:
                        print(f"First row: {rows[0]}")
            except Exception as e:
                print(f"SQLAlchemy error: {e}")
                # Fallback: используем raw SQLite
                import sqlite3
                db_path = str(self.engine.url).replace("sqlite:///", "")
                print(f"Trying raw SQLite with path: {db_path}")
                con = sqlite3.connect(db_path)
                cur = con.cursor()
                try:
                    cur.execute(query, params)
                    rows = cur.fetchall()
                    print(f"Raw SQLite returned {len(rows)} rows")
                finally:
                    con.close()
            
            # Конвертируем в словари
            events = []
            for row in rows:
                event_dict = {
                    "id": row[0],
                    "title": row[1],
                    "desc": row[2],
                    "start": row[3],
                    "end": row[4],
                    "time_str": row[5],
                    "venue": row[6],
                    "area": row[7],
                    "address": row[8],
                    "image": row[9],
                    "url": row[10],
                    "price_min": row[11],
                    "categories": self._parse_json_field(row[12]),
                    "tags": self._parse_json_field(row[13]),
                    "attrs": self._parse_json_field(row[14]),
                    "source": row[15],
                    "fetched_at": row[16],
                    "raw_html_ref": row[17],
                    "city": row[18],
                }
                events.append(event_dict)
            
            logger.info(f"Loaded {len(events)} events from database for category: {category}")
            return events
            
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return []
    
    def healthcheck(self) -> bool:
        """Database health check."""
        return healthcheck()
    
    def _parse_json_field(self, value: Optional[str]) -> Any:
        """Parse JSON field from database."""
        if not value:
            return []
        try:
            return json.loads(value)
        except Exception:
            return []
