#!/usr/bin/env python
from __future__ import annotations
import json, os, sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Tuple
import sqlite3
import redis

CITY = os.environ.get("CITY", "bangkok")
DB_URL = os.environ.get("DB_URL")
REDIS_URL = os.environ.get("REDIS_URL")
TTL_S = int(os.environ.get("CACHE_TTL_S", "1200"))

# Деривация флагов из тегов (на случай, когда в attrs их нет)
DERIVED_FLAGS_FROM_TAGS = {
    "live_music": {"live music", "music", "concert"},
    "indoor": {"indoor"},
    "art": {"art", "art & culture", "exhibition"},
    "culture": {"culture", "cultural"},
}

def _db_path_from_url(url: str) -> str:
    if not url or not url.startswith("sqlite:////"):
        raise RuntimeError("DB_URL must be sqlite:////ABS_PATH for this utility")
    return url.replace("sqlite:////", "")

def _date_utc(dt_str: str) -> str:
    # dt_str like '2025-08-31 12:00:00+00:00' or ISO
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        # last resort: cut off timezone
        dt = datetime.fromisoformat(dt_str.split("+")[0])
    return dt.date().isoformat()

def load_events(db_path: str, day_from: str, day_to: str, city: str) -> List[Tuple[str, str, str, str, str]]:
    """
    returns list of (id, start, categories_json, attrs_json, tags_json)
    """
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    # фильтруем по дате start и городу, если столбец есть
    cols = {r[1] for r in cur.execute("PRAGMA table_info(events)").fetchall()}
    if "city" in cols:
        rows = cur.execute(
            "SELECT id, start, categories, attrs, tags FROM events WHERE date(start) BETWEEN ? AND ? AND city = ?",
            (day_from, day_to, city),
        ).fetchall()
    else:
        rows = cur.execute(
            "SELECT id, start, categories, attrs, tags FROM events WHERE date(start) BETWEEN ? AND ?",
            (day_from, day_to),
        ).fetchall()
    con.close()
    return rows

def main() -> None:
    if not DB_URL or not REDIS_URL:
        raise RuntimeError("Missing DB_URL or REDIS_URL")
    db_path = _db_path_from_url(DB_URL)
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    days = int(os.environ.get("DAYS_AHEAD", "7"))
    today = datetime.now(timezone.utc).date()
    day_from = today.isoformat()
    day_to = (today + timedelta(days=days)).isoformat()

    rows = load_events(db_path, day_from, day_to, CITY)
    # day → {cat: [ids]}, day → {flag: [ids]}, встреченные имена флагов
    by_cat: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
    by_flag: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
    seen_flags: set[str] = set()

    for ev_id, start, cats_json, attrs_json, tags_json in rows:
        day = _date_utc(start)
        
        cats = []
        try:
            cats = list(dict.fromkeys(json.loads(cats_json or "[]")))
        except Exception:
            pass
        attrs: Dict[str, Any] = {}
        try:
            attrs = json.loads(attrs_json or "{}")
        except Exception:
            pass
        tags = []
        try:
            tags = [t.strip().lower() for t in json.loads(tags_json or "[]")]
        except Exception:
            pass

        for c in cats:
            key = c.strip().lower()
            if key:
                by_cat[day][key].append(ev_id)
        
        # 1) флаги из attrs (boolean)
        for f, v in (attrs or {}).items():
            if isinstance(v, bool) and v:
                fname = f.strip().lower()
                seen_flags.add(fname)
                by_flag[day][fname].append(ev_id)
        # 2) деривация некоторых флагов по тегам (если их нет в attrs)
        tagset = set(tags)
        for fname, syns in DERIVED_FLAGS_FROM_TAGS.items():
            if not attrs.get(fname) and tagset.intersection(syns):
                seen_flags.add(fname)
                by_flag[day][fname].append(ev_id)

    # запись ключей + индексов (включая дни с одними флагами)
    total_keys = 0
    all_days = sorted(set(by_cat.keys()) | set(by_flag.keys()))
    for day in all_days:
        cats = by_cat.get(day, {})
        flags = by_flag.get(day, {})
        # categories
        for c, ids in cats.items():
            k = f"{CITY}:{day}:{c}"
            r.setex(k, TTL_S, json.dumps(ids))
            total_keys += 1
        # flags
        for f, ids in flags.items():
            k = f"{CITY}:{day}:flag:{f}"
            r.setex(k, TTL_S, json.dumps(ids))
            total_keys += 1
        # index
        idx = {
            "categories": {c: len(ids) for c, ids in cats.items()},
            "flags": {f: len(ids) for f, ids in flags.items()},
            "all_flags": sorted(list(seen_flags)),
        }
        r.setex(f"{CITY}:{day}:index", TTL_S, json.dumps(idx))
        total_keys += 1

    print(f"Rebuilt keys: {total_keys} for days {day_from}..{day_to} city={CITY}")

if __name__ == "__main__":
    main()
